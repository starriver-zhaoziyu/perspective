/******************************************************************************
 *
 * Copyright (c) 2017, the Perspective Authors.
 *
 * This file is part of the Perspective library, distributed under the terms of
 * the Apache License 2.0.  The full license can be found in the LICENSE file.
 *
 */

/******************************************************************************
 *
 * Constants
 *
 */

const CSV = "https://unpkg.com/@jpmorganchase/perspective-examples@0.2.0-beta.2/build/superstore.csv";
const ARROW = "https://unpkg.com/@jpmorganchase/perspective-examples@0.2.0-beta.2/build/superstore.arrow";

const AGG_OPTIONS = [[{column: "Sales", op: "sum"}], [{column: "State", op: "dominant"}], [{column: "Order Date", op: "dominant"}]];
const COLUMN_PIVOT_OPTIONS = [[], ["Sub-Category"]];
const ROW_PIVOT_OPTIONS = [[], ["State"], ["State", "City"]];
const COLUMN_TYPES = {Sales: "number", "Order Date": "datetime", State: "string"};

const COMPUTED_FUNCS = {
    "+": (x, y) => x + y,
    "-": (x, y) => x - y,
    "*": (x, y) => x * y,
    "/": (x, y) => x / y,
    pow2: x => Math.pow(x, 2),
    sqrt: x => Math.sqrt(x),
    uppercase: x => x.toUpperCase(),
    concat_comma: (x, y) => x + y,
    week_bucket: x => {
        let date = new Date(x);
        let day = date.getDay();
        let diff = date.getDate() - day + (day == 0 ? -6 : 1);
        date.setHours(0);
        date.setMinutes(0);
        date.setSeconds(0);
        date.setDate(diff);
        return date;
    }
};

const COMPUTED_CONFIG = {computed_function_name: "+", column: "computed", inputs: ["Sales", "Profit"]};

const COMPLEX_COMPUTED_CONFIGS = {
    numeric: [
        {computed_function_name: "*", column: "computed", inputs: ["Sales", "Profit"]},
        {computed_function_name: "sqrt", column: "computed2", inputs: ["computed"]},
        {computed_function_name: "+", column: "computed3", inputs: ["computed2", "Sales"]},
        {computed_function_name: "*", column: "computed4", inputs: ["Profit", "Quantity"]},
        {computed_function_name: "abs", column: "computed5", inputs: ["computed4"]},
        {computed_function_name: "-", column: "computed6", inputs: ["computed5", "computed"]}
    ],
    string: [
        {computed_function_name: "uppercase", column: "computed", inputs: ["City"]},
        {computed_function_name: "lowercase", column: "computed2", inputs: ["Customer ID"]},
        {computed_function_name: "lowercase", column: "computed3", inputs: ["Order ID"]},
        {computed_function_name: "is", column: "computed4", inputs: ["computed", "computed2"]},
        {computed_function_name: "concat_comma", column: "computed5", inputs: ["computed2", "computed3"]},
        {computed_function_name: "concat_space", column: "computed6", inputs: ["State", "City"]}
    ],
    datetime: [
        {computed_function_name: "day_bucket", column: "computed", inputs: ["Order Date"]},
        {computed_function_name: "second_bucket", column: "computed2", inputs: ["Order Date"]},
        {computed_function_name: "day_of_week", column: "computed3", inputs: ["computed2"]},
        {computed_function_name: "month_of_year", column: "computed4", inputs: ["Ship Date"]},
        {computed_function_name: "year_bucket", column: "computed5", inputs: ["computed2"]},
        {computed_function_name: "minute_bucket", column: "computed6", inputs: ["computed2"]}
    ]
};

const SIMPLE_EXPRESSION = ['// computed \n "Sales" + "Profit"'];

const COMPLEX_EXPRESSIONS = {
    numeric: ['sqrt("Sales" * "Profit") + "Sales"', 'abs("Profit" * "Quantity")', 'abs("Profit" * "Quantity") - (sqrt("Sales" * "Profit") + "Sales")'],
    string: [
        'upper("City")',
        'lower("Customer ID")',
        'lower("Order ID")',
        'upper("City") == lower("Customer ID")',
        `concat(lower("Customer ID"), ', ', lower("Order ID"))`,
        `concat("State", ' ', "City")`
    ],
    datetime: [
        `bucket("Order Date", 'D')`,
        `// computed2\n bucket("Order Date", 'S')`,
        `day_of_week("computed2")`,
        `month_of_year("Ship Date")`,
        `bucket("computed2", 'Y')`,
        `bucket("computed2", 'm')`
    ]
};

/******************************************************************************
 *
 * Perspective.js Benchmarks
 *
 */

PerspectiveBench.setIterations(100);
PerspectiveBench.setTimeout(2000);
PerspectiveBench.setToss(5);

let worker, data;

beforeAll(async () => {
    await load_dynamic_browser("perspective", PerspectiveBench.commandArg(0));
    window.perspective = window.perspective.default || window.perspective;
    worker = window.perspective.worker();
    await wait_for_perspective();
    if (typeof module !== "undefined" && module.exports) {
        data = await get_data_node(worker);
    } else {
        data = await get_data_browser(worker);
    }
});

describe("Table", async () => {
    let table;

    afterEach(async () => {
        await table.delete();
    });

    for (const name of Object.keys(data)) {
        describe("mixed", async () => {
            describe("table", () => {
                benchmark(name, async () => {
                    let test = data[name];
                    table = await worker.table(test.slice ? test.slice() : test);
                    await table.size();
                });
            });
        });
    }
});

describe("Update", async () => {
    // Generate update data from Perspective
    const static_table = await worker.table(data.arrow.slice());
    const static_view = await static_table.view();

    let table, view;

    afterEach(async () => {
        if (view) {
            await view.delete();
        }
        await table.delete();
    });

    for (const name of Object.keys(data)) {
        describe("mixed", async () => {
            // Benchmark how long it takes the table to update without any
            // linked contexts to notify.
            describe("table_only", async () => {
                table = await worker.table(data.arrow.slice());

                let test_data = await static_view[`to_${name}`]({end_row: 500});
                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await table.size();
                    }
                });
            });

            describe("ctx0", async () => {
                table = await worker.table(data.arrow.slice());
                view = await table.view();

                const test_data = await static_view[`to_${name}`]({end_row: 500});

                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });

            describe("ctx0 sorted", async () => {
                table = worker.table(data.arrow.slice());
                view = table.view({
                    sort: [["Customer Name", "desc"]]
                });

                const test_data = await static_view[`to_${name}`]({end_row: 500});

                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });

            describe("ctx0 sorted deep", async () => {
                table = worker.table(data.arrow.slice());
                //table_indexed = worker.table(data.arrow.slice(), {index: "Row ID"});
                view = table.view({
                    sort: [
                        ["Customer Name", "desc"],
                        ["Order Date", "asc"]
                    ]
                });

                const test_data = await static_view[`to_${name}`]({end_row: 500});
                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });

            describe("ctx1", async () => {
                table = await worker.table(data.arrow.slice());
                view = await table.view({
                    row_pivots: ["State"]
                });

                let test_data = await static_view[`to_${name}`]({end_row: 500});
                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });

            describe("ctx1 deep", async () => {
                table = await worker.table(data.arrow.slice());
                view = await table.view({
                    row_pivots: ["State", "City"]
                });
                let test_data = await static_view[`to_${name}`]({end_row: 500});
                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });

            describe("ctx2", async () => {
                table = await worker.table(data.arrow.slice());
                view = await table.view({
                    row_pivots: ["State"],
                    column_pivots: ["Sub-Category"]
                });
                let test_data = await static_view[`to_${name}`]({end_row: 500});
                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });

            describe("ctx2 deep", async () => {
                table = await worker.table(data.arrow.slice());
                view = await table.view({
                    row_pivots: ["State", "City"],
                    column_pivots: ["Sub-Category"]
                });
                let test_data = await static_view[`to_${name}`]({end_row: 500});
                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });

            describe("ctx1.5", async () => {
                table = await worker.table(data.arrow.slice());
                view = await table.view({
                    column_pivots: ["Sub-Category"]
                });
                let test_data = await static_view[`to_${name}`]({end_row: 500});
                benchmark(name, async () => {
                    for (let i = 0; i < 5; i++) {
                        table.update(test_data.slice ? test_data.slice() : test_data);
                        await view.num_rows();
                    }
                });
            });
        });
    }
});

describe("Deltas", async () => {
    // Generate update data from Perspective
    const static_table = await worker.table(data.arrow.slice());
    const static_view = await static_table.view();

    let table, view;

    afterEach(async () => {
        await view.delete();
        await table.delete();
    });

    describe("mixed", async () => {
        describe("ctx0", async () => {
            table = await worker.table(data.arrow.slice());
            view = await table.view();
            view.on_update(() => {}, {mode: "row"});
            const test_data = await static_view.to_arrow({end_row: 500});
            benchmark("row delta", async () => {
                for (let i = 0; i < 3; i++) {
                    table.update(test_data.slice ? test_data.slice() : test_data);
                    await table.size();
                }
            });
        });

        describe("ctx1", async () => {
            table = await worker.table(data.arrow.slice());
            view = await table.view({
                row_pivots: ["State"]
            });
            view.on_update(() => {}, {mode: "row"});
            const test_data = await static_view.to_arrow({end_row: 500});
            benchmark("row delta", async () => {
                for (let i = 0; i < 3; i++) {
                    table.update(test_data.slice());
                    await table.size();
                }
            });
        });

        describe("ctx1 deep", async () => {
            table = await worker.table(data.arrow.slice());
            view = await table.view({
                row_pivots: ["State", "City"]
            });
            view.on_update(() => {}, {mode: "row"});
            const test_data = await static_view.to_arrow({end_row: 500});
            benchmark("row delta", async () => {
                for (let i = 0; i < 3; i++) {
                    table.update(test_data.slice());
                    await table.size();
                }
            });
        });

        describe("ctx2", async () => {
            table = await worker.table(data.arrow.slice());
            view = await table.view({
                row_pivots: ["State"],
                column_pivots: ["Sub-Category"]
            });
            view.on_update(() => {}, {mode: "row"});
            const test_data = await static_view.to_arrow({end_row: 500});
            benchmark("row delta", async () => {
                for (let i = 0; i < 3; i++) {
                    table.update(test_data.slice());
                    await table.size();
                }
            });
        });

        describe("ctx2 deep", async () => {
            table = await worker.table(data.arrow.slice());
            view = await table.view({
                row_pivots: ["State", "City"],
                column_pivots: ["Sub-Category"]
            });
            view.on_update(() => {}, {mode: "row"});
            const test_data = await static_view.to_arrow({end_row: 500});
            benchmark("row delta", async () => {
                for (let i = 0; i < 3; i++) {
                    table.update(test_data.slice());
                    await table.size();
                }
            });
        });

        describe("ctx1.5", async () => {
            table = await worker.table(data.arrow.slice());
            view = await table.view({
                column_pivots: ["Sub-Category"]
            });
            view.on_update(() => {}, {mode: "row"});
            const test_data = await static_view.to_arrow({end_row: 500});
            benchmark("row delta", async () => {
                for (let i = 0; i < 3; i++) {
                    table.update(test_data.slice());
                    await table.size();
                }
            });
        });
    });
});

describe("View", async () => {
    let table;

    beforeAll(async () => {
        table = await worker.table(data.arrow.slice());
    });

    afterAll(async () => {
        await table.delete();
    });

    for (const aggregate of AGG_OPTIONS) {
        for (const row_pivot of ROW_PIVOT_OPTIONS) {
            for (const column_pivot of COLUMN_PIVOT_OPTIONS) {
                const config = {aggregate, row_pivot, column_pivot};

                const [cat, type] = to_name(config);

                describe(type, async () => {
                    describe(cat, async () => {
                        let view;

                        afterEach(async () => {
                            await view.delete();
                        });

                        benchmark(`view`, async () => {
                            view = await table.view(config);
                            await view.schema();
                        });
                    });

                    describe(`${cat} sorted`, async () => {
                        let view;

                        afterEach(async () => {
                            await view.delete();
                        });

                        benchmark(`sorted float asc`, async () => {
                            view = table.view({
                                aggregate,
                                row_pivot,
                                column_pivot,
                                sort: [["Sales", "asc"]]
                            });
                            await view.schema();
                        });

                        benchmark(`sorted float desc`, async () => {
                            view = table.view({
                                aggregate,
                                row_pivot,
                                column_pivot,
                                sort: [["Sales", "asc"]]
                            });
                            await view.schema();
                        });

                        benchmark(`sorted str asc`, async () => {
                            view = table.view({
                                aggregate,
                                row_pivot,
                                column_pivot,
                                sort: [["Customer Name", "asc"]]
                            });
                            await view.schema();
                        });

                        benchmark(`sorted str desc`, async () => {
                            view = table.view({
                                aggregate,
                                row_pivot,
                                column_pivot,
                                sort: [["Customer Name", "desc"]]
                            });
                            await view.schema();
                        });
                    });

                    describe(cat, async () => {
                        let view;

                        beforeAll(async () => {
                            view = await table.view(config);
                            await view.schema();
                        });

                        afterAll(async () => {
                            await view.delete();
                        });

                        for (const format of ["json", "columns", "arrow"]) {
                            benchmark(format, async () => {
                                await view[`to_${format}`]();
                            });
                        }
                    });
                });
            }
        }
    }
});

describe("Expression/Computed Column", async () => {
    for (const name of Object.keys(COMPUTED_FUNCS)) {
        describe("mixed", async () => {
            // Use a single source table for computed
            let table;

            afterEach(async () => {
                await table.delete();
            });

            COMPUTED_CONFIG.computed_function_name = name;

            switch (name) {
                case "pow2":
                case "sqrt":
                    {
                        COMPUTED_CONFIG.inputs = ["Sales"];
                    }
                    break;
                case "uppercase":
                    {
                        COMPUTED_CONFIG.inputs = ["Customer Name"];
                    }
                    break;
                case "concat_comma":
                    {
                        COMPUTED_CONFIG.inputs = ["State", "City"];
                    }
                    break;
                case "week_bucket":
                    {
                        COMPUTED_CONFIG.inputs = ["Order Date"];
                    }
                    break;
                default: {
                    COMPUTED_CONFIG.inputs = ["Sales", "Profit"];
                }
            }

            describe("ctx0", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());
                let add_computed_method;

                if (table.add_computed) {
                    add_computed_method = table.add_computed;
                }

                benchmark(`computed: \`${name}\``, async () => {
                    if (add_computed_method) {
                        COMPUTED_CONFIG.func = COMPUTED_FUNCS[name];
                        COMPUTED_CONFIG.type = "float";

                        table = table.add_computed([COMPUTED_CONFIG]);
                    } else {
                        let config = {};
                        if (view.expression_schema) {
                            // New expressions API
                            config.expressions = SIMPLE_EXPRESSION;
                        } else {
                            // Old computed_columns API
                            config.computed_columns = [COMPUTED_CONFIG];
                        }

                        view = await table.view(config);
                    }

                    // must process update
                    await table.size();
                });

                if (!add_computed_method) {
                    benchmark(`sort computed: \`${name}\``, async () => {
                        let config = {
                            sort: [["computed", "desc"]]
                        };

                        if (view.expression_schema) {
                            // New expressions API
                            config.expressions = SIMPLE_EXPRESSION;
                        } else {
                            // Old computed_columns API
                            config.computed_columns = [COMPUTED_CONFIG];
                        }

                        view = await table.view(config);

                        await table.size();
                    });
                }
            });

            describe("ctx1", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());

                if (table.add_computed) {
                    console.error("Not running pivoted computed column benchmarks on versions before 0.5.0.");
                    return;
                }

                benchmark(`row pivot computed: \`${name}\``, async () => {
                    let config = {
                        row_pivots: ["computed"]
                    };

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = SIMPLE_EXPRESSION;
                    } else {
                        // Old computed_columns API
                        config.computed_columns = [COMPUTED_CONFIG];
                    }

                    view = await table.view(config);

                    await table.size();
                });
            });

            describe("ctx2", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());

                if (table.add_computed) {
                    console.error("Not running pivoted computed column benchmarks on versions before 0.5.0.");
                    return;
                }

                benchmark(`row and column pivot computed: \`${name}\``, async () => {
                    let config = {
                        row_pivots: ["computed"],
                        column_pivots: ["computed"]
                    };

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = SIMPLE_EXPRESSION;
                    } else {
                        // Old computed_columns API
                        config.computed_columns = [COMPUTED_CONFIG];
                    }

                    view = await table.view(config);

                    await table.size();
                });
            });

            describe("ctx1.5", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());

                if (table.add_computed) {
                    console.error("Not running pivoted computed column benchmarks on versions before 0.5.0.");
                    return;
                }

                benchmark(`column pivot computed: \`${name}\``, async () => {
                    let config = {
                        column_pivots: ["computed"]
                    };

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = SIMPLE_EXPRESSION;
                    } else {
                        // Old computed_columns API
                        config.computed_columns = [COMPUTED_CONFIG];
                    }

                    view = await table.view(config);

                    await table.size();
                });
            });
        });
    }

    // multi-dependency computed columns
    for (const name in COMPLEX_COMPUTED_CONFIGS) {
        describe("mixed", async () => {
            // Use a single source table for computed
            let table;

            afterEach(async () => {
                await table.delete();
            });

            describe("ctx0", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());

                if (table.add_computed) {
                    console.error("Cannot run complex computed column benchmarks on versions before 0.5.0.");
                    return;
                }

                benchmark(`computed complex: \`${name}\``, async () => {
                    let config = {};

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = COMPLEX_EXPRESSIONS[name];
                    } else {
                        // Old computed_columns API
                        config.computed_columns = COMPLEX_COMPUTED_CONFIGS[name];
                    }

                    view = await table.view(config);

                    await table.size();
                });

                benchmark(`sort computed complex: \`${name}\``, async () => {
                    let config = {};

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = COMPLEX_EXPRESSIONS[name];
                        config.sort = [[COMPLEX_EXPRESSIONS[name][0], "desc"]];
                    } else {
                        // Old computed_columns API
                        config.computed_columns = COMPLEX_COMPUTED_CONFIGS[name];
                        config.sort = [["computed", "desc"]];
                    }

                    view = await table.view(config);

                    await table.size();
                });
            });

            describe("ctx1", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());

                if (table.add_computed) {
                    console.error("Cannot run complex computed column benchmarks on versions before 0.5.0.");
                    return;
                }

                benchmark(`row pivot computed complex: \`${name}\``, async () => {
                    let config = {};

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = COMPLEX_EXPRESSIONS[name];
                        config.row_pivots = [COMPLEX_EXPRESSIONS[name][0]];
                    } else {
                        // Old computed_columns API
                        config.computed_columns = COMPLEX_COMPUTED_CONFIGS[name];
                        config.row_pivots = ["computed"];
                    }

                    view = await table.view(config);
                    await table.size();
                });
            });

            describe("ctx2", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());

                if (table.add_computed) {
                    console.error("Cannot run complex computed column benchmarks on versions before 0.5.0.");
                    return;
                }

                benchmark(`row and column pivot computed complex: \`${name}\``, async () => {
                    let config = {};

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = COMPLEX_EXPRESSIONS[name];
                        config.row_pivots = [COMPLEX_EXPRESSIONS[name][0]];
                        config.column_pivots = [COMPLEX_EXPRESSIONS[name][1]];
                    } else {
                        // Old computed_columns API
                        config.computed_columns = COMPLEX_COMPUTED_CONFIGS[name];
                        config.row_pivots = ["computed"];
                        config.column_pivots = ["computed2"];
                    }

                    view = await table.view(config);
                    await table.size();
                });
            });

            describe("ctx1.5", async () => {
                let view;

                afterEach(async () => {
                    if (view) {
                        await view.delete();
                    }
                });

                table = await worker.table(data.arrow.slice());

                if (table.add_computed) {
                    console.error("Cannot run complex computed column benchmarks on versions before 0.5.0.");
                    return;
                }

                benchmark(`column pivot computed complex: \`${name}\``, async () => {
                    let config = {};

                    if (view.expression_schema) {
                        // New expressions API
                        config.expressions = COMPLEX_EXPRESSIONS[name];
                        config.column_pivots = [COMPLEX_EXPRESSIONS[name][0]];
                    } else {
                        // Old computed_columns API
                        config.computed_columns = COMPLEX_COMPUTED_CONFIGS[name];
                        config.column_pivots = ["computed"];
                    }

                    view = await table.view(config);
                    await table.size();
                });
            });
        });
    }
});

/******************************************************************************
 *
 * Utils
 *
 */

const wait_for_perspective = () => new Promise(resolve => window.addEventListener("perspective-ready", resolve));

function to_name({aggregate, row_pivot, column_pivot}) {
    const type = COLUMN_TYPES[aggregate[0].column];
    const sides = {
        "00": "ctx0",
        "10": "ctx1",
        "20": "ctx1 deep",
        "21": "ctx2 deep",
        "11": "ctx2",
        "01": "ctx1.5"
    }[row_pivot.length.toString() + column_pivot.length.toString()];
    return [`${sides}`, type];
    //    return `${COLUMN_TYPES[aggregate[0].column]},${row_pivot.join("/") || "-"}*${column_pivot.join("/") || "-"}`;
}

const load_dynamic_node = name => {
    return new Promise(resolve => {
        window.perspective = require("@finos/perspective");
        resolve();
    });
};

const load_dynamic_browser = (name, url) => {
    return new Promise(resolve => {
        const existingScript = document.getElementById(name);
        if (!existingScript) {
            const script = document.createElement("script");
            script.src = url; // URL for the third-party library being loaded.
            script.id = name; // e.g., googleMaps or stripe
            document.body.appendChild(script);
            script.onload = () => {
                if (resolve) resolve();
            };
        } else {
            resolve();
        }
    });
};

async function get_data_browser(worker) {
    const req1 = fetch(CSV);
    const req2 = fetch(ARROW);

    console.log("Downloading CSV");
    let content = await req1;
    const csv = await content.text();

    console.log("Downloading Arrow");
    content = await req2;
    const arrow = await content.arrayBuffer();

    console.log("Generating JSON");
    const tbl = await worker.table(arrow.slice());
    const view = await tbl.view();
    const json = await view.to_json();
    const columns = await view.to_columns();
    view.delete();
    tbl.delete();

    return {csv, arrow, json, columns};
}

async function get_data_node(worker) {
    const fs = require("fs");
    const path = require("path");

    const ARROW_FILE = path.resolve(__dirname, "../../../../examples/simple/superstore.arrow");
    console.log("Loading Arrow");
    const arrow = fs.readFileSync(ARROW_FILE, null).buffer;

    console.log("Generating JSON");
    const tbl = await worker.table(arrow.slice());
    const view = tbl.view();
    const rows = await view.to_json();
    const columns = await view.to_columns();
    const csv = await view.to_csv();
    view.delete();
    tbl.delete();

    return {csv, arrow, rows, columns};
}
