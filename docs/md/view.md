---
id: view
title: View
---

<script src="../../../../js/index.js"></script>
<link rel="stylesheet" href="../../../../css/concepts/index.css">

The View is Perspective's query and serialization interface. It represents a
query on the `Table`'s dataset and is always created from an existing `Table`
instance via the `view()` method with a set of
[`View` configuration parameters](https://perspective.finos.org/docs/obj/perspective.html#module_perspective..table+view):

```javascript
const table = await perspective.table({
    id: [1, 2, 3, 4],
    name: ["a", "b", "c", "d"]
});

const view = await table.view({columns: ["name"]});
const json = await view.to_json();

view.delete();
```

```python
const table = perspective.Table({
    "id": [1, 2, 3, 4],
    "name": ["a", "b", "c", "d"]
});

view = table.view(columns=["name"]);
arrow = view.to_arrow();
```

`View` objects are immutable with respect to the arguments provided to the
`view()` method;  to change these parameters, you must create a new `View` on
the same `Table`.  However, each `View` is _live_ with respect to the `Table`'s
data, and will (within a conflation window) update with the latest state as its
parent `Table` updates, including incrementally recalculating all
aggregates, pivots, filters, etc. `View` query parameters are composable,
in that each parameter works independently _and_ in conjunction
with each other, and there is no limit to the number of pivots, filters, etc.
which can be applied.

> Examples in this section are live — play around with each
`<perspective-viewer>` instance to see how different query parameters affect
what you see!

### Querying data with `view()`

To query the table, create a `view()` on the table instance with an optional
configuration object.  A `table()` can have as many `view()`s associated with
it as you need - Perspective conserves memory by relying on a single `table()`
to power multiple `view()`s concurrently:

```javascript
const view = await table.view({
    columns: ["Sales"],
    aggregates: {Sales: "sum"},
    row_pivot: ["Region", "Country"],
    filter: [["Category", "in", ["Furniture", "Technology"]]]
});
```

```python
view = table.view(
    columns=["Sales"],
    aggregates={"Sales": "sum"},
    row_pivot=["Region", "Country"],
    filter=[["Category", "in", ["Furniture", "Technology"]]]
)
```

See the [View API documentation](/docs/obj/perspective.html) for more details.
## Row Pivots

A row pivot _groups_ the dataset by the unique values of each column used as a
row pivot - a close analogue in SQL to the `GROUP BY` statement.  The underlying
dataset is aggregated to show the values belonging to each group, and a total
row is calculated for each group, showing the currently selected aggregated
value (e.g. `sum`) of the column. Row pivots are useful for
hierarchies, categorizing data and attributing values, i.e. showing the number
of units sold based on State and City.  In Perspective, row pivots are 
represented as an array of string column names to pivot, are applied in the 
order provided;  For example, a row
pivot of `["State", "City", "Neighborhood"]` shows the values for each
neighborhood, which are grouped by City, which are in turn grouped by State.

```javascript
const view = await table.view({row_pivots: ["a", "c"]});
```

```python
view = table.view(row_pivots=["a", "c"])
```

#### Example

```html
<perspective-viewer
    row-pivots='["State", "City"]'
    columns='["Sales", "Profit"]'>
</perspective-viewer>
```

<div>
<perspective-viewer row-pivots='["State", "City"]' columns='["Sales", "Profit"]'>
</perspective-viewer>
</div>

## Column Pivots

A column pivot _splits_ the dataset by the unique values of each column used as
a column pivot. The underlying dataset is not aggregated, and a new column is
created for each unique value of the column pivot. Each newly created column
contains the parts of the dataset that correspond to the column header, i.e.
a `View` that has `["State"]` as its column pivot will have a new column for
each state.  In Perspective, column pivots are represented as an array of string
column names to pivot:

```javascript
const view = await table.view({column_pivots: ["a", "c"]});
```

```python
view = table.view(column_pivots=["a", "c"])
```

#### Example

```html
<perspective-viewer
    row-pivots='["Category"]'
    column-pivots='["Region"]'
    columns='["Sales", "Profit"]'>
</perspective-viewer>
```

<div>
<perspective-viewer row-pivots='["Category"]' column-pivots='["Region"]' columns='["Sales", "Profit"]'>
</perspective-viewer>
</div>

## Aggregates

Aggregates perform a calculation over an entire column, and are displayed when
one or more [Row Pivots](#row-pivots) are applied to the `View`. Aggregates can
be specified by the user, or Perspective will use the following sensible default
aggregates based on column type:

- "sum" for `integer` and `float` columns
- "count" for all other columns

Perspective provides a selection of aggregate functions that can be
applied to columns in the `View` constructor using a dictionary of column
name to aggregate function name:

```javascript
const view = await table.view({
    aggregates: {
        a: "avg",
        b: "distinct count"
    }
});
```

```python
view = table.view(
    aggregates={
        "a": "avg",
        "b": "distinct count"
    }
)
```

#### Example

```html
<perspective-viewer
    aggregates='{"Sales": "avg", "Profit", "median"}'
    row-pivots='["State", "City"]'
    columns='["Sales", "Profit"]'>
</perspective-viewer>
```

<div>
<perspective-viewer aggregates='{"Sales": "avg", "Profit": "median"}' row-pivots='["State", "City"]' columns='["Sales", "Profit"]'>
</perspective-viewer>
</div>

## Columns

The `columns` property specifies which columns should be included in the
`View`'s output. This allows users to show or hide a specific subset of columns,
as well as control the order in which columns appear to the user.  This is
represented in Perspective as an array of string column names:

```javascript
const view = await table.view({
    columns: ["a"]
});
```

```python
view = table.view(columns=["a"])
```

#### Example

```html
<perspective-viewer
    columns='["Sales", "Profit", "Segment"]'>
</perspective-viewer>
```

<div>
<perspective-viewer columns='["Sales", "Profit", "Segment"]'>
</perspective-viewer>
</div>

## Sort

The `sort` property specifies columns on which the query should be sorted,
analogous to `ORDER BY` in SQL. A column can be sorted regardless of its
data type, and sorts can be applied in ascending or descending order.
Perspective represents `sort` as an array of arrays, with the values of each
inner array being a string column name and a string sort direction.
When `column-pivots` are applied, the additional sort directions `"col asc"` and
`"col desc"` will determine the order of pivot columns groups.

```javascript
const view = await table.view({
    sort: [["a", "asc"]]
});
```

```python
view = table.view(sort=[["a", "asc"]])
```

#### Example

```html
<perspective-viewer
    columns='["Sales", "Profit"]'
    sort='[["Sales", "desc"]]'>
</perspective-viewer>
```

<div>
<perspective-viewer columns='["Sales", "Profit"]' sort='[["Sales", "desc"]]'>
</perspective-viewer>
</div>

## Filter

The `filter` property specifies columns on which the query can be filtered,
returning rows that pass the specified filter condition. This is analogous
to the `WHERE` clause in SQL. There is no limit on the number of columns
where `filter` is applied, but the resulting dataset is one that passes
all the filter conditions, i.e. the filters are joined with an `AND` condition.

Perspective represents `filter` as an array of arrays, with the values of each
inner array being a string column name, a string filter operator, and a filter
operand in the type of the column:

```javascript
const view = await table.view({
    filter: [["a", "<", 100]]
});
```

```python
view = table.view(filter=[["a", "<", 100]])
```

#### Example

Use the `filters` attribute on `<perspective-viewer>` instead of `filter`.

```html
<perspective-viewer
    columns='["Sales", "Profit"]'
    filters='[["State", "==", "Texas"]]'>
</perspective-viewer>
```

<div>
<perspective-viewer columns='["Sales", "Profit"]' filters='[["State","==","Texas"]]'>
</perspective-viewer>
</div>

## Computed Columns

The `computed-columns` property defines calculations over the Table's columns,
allowing you to create new columns using values from existing ones.  Computed
columns are added using the `New Column` button in
the bottom left of `<perspective-viewer>`, which opens the expression editor.
This allows you to create computed columns from arbitary expressions, which are
type and syntax-checked and allow for aliasing, nesting, and evaluation in the
correct order.  To add computed columns in via the API, pass in an array of
Objects:
#### Example

`<perspective-viewer>`'s `computed-column` attribute can be set using an
array of expressions.

```html
<perspective-viewer
    columns='["(Sales + ((Profit * Quantity) / sqrt(Sales)))"]'
    computed-columns='["\"Sales\" + \"Profit\" * \"Quantity\" / sqrt(\"Sales\")")]'>
</perspective-viewer>
```

<div>
<perspective-viewer columns='["(Sales + ((Profit * Quantity) / sqrt(Sales)))"]' computed-columns='["\"Sales\" + \"Profit\" * \"Quantity\" / sqrt(\"Sales\")"]'>
</perspective-viewer>
</div>

## Flattening a `view()` into a `table()`

In Javascript, a `table()` can be constructed on a `view()` instance, which
will return a new `table()` based on the `view()`'s dataset, and all future
updates that affect the `view()` will be forwarded to the new `table()`. This
is particularly useful for implementing a
[Client/Server Replicated](docs/md/server.html#clientserver-replicated) design,
by serializing the `View` to an arrow and setting up an `on_update` callback:

```javascript
const worker1 = perspective.worker();
const table = await worker.table(data);
const view = await table.view({filter: [["State", "==", "Texas"]]});
const table2 = await worker.table(view);

table.update([{State: "Texas", City: "Austin"}]);
```

```python
table = perspective.Table(data);
view = table.view(filter=[["State", "==", "Texas"]])
table2 = perspective.Table(view.to_arrow());

def updater(port, delta):
    table2.update(delta)

view.on_update(updater, mode="Row")

table.update([{"State": "Texas", "City": "Austin"}])
```