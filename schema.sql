CREATE SEQUENCE IF NOT EXISTS seq_commit_id START 1;

CREATE TABLE IF NOT EXISTS tool_catalog (
    tool_id VARCHAR PRIMARY KEY,
    server_namespace VARCHAR,
    tool_name VARCHAR,
    category VARCHAR,
    description VARCHAR,
    parameters_schema_json VARCHAR,
    token_cost_estimate INTEGER,
    content_hash VARCHAR,
    indexed_at_utc VARCHAR
);

CREATE TABLE IF NOT EXISTS routing_benchmarks (
    query_id VARCHAR PRIMARY KEY,
    user_intent VARCHAR,
    routed_tool_ids_json VARCHAR,
    token_budget_unfiltered INTEGER,
    token_budget_routed INTEGER,
    token_savings_pct DOUBLE,
    evaluated_at_utc VARCHAR
);

CREATE TABLE IF NOT EXISTS multiplexer_ledger (
    commit_id BIGINT PRIMARY KEY,
    timestamp_utc VARCHAR,
    operation VARCHAR,
    tool_id VARCHAR,
    server_namespace VARCHAR,
    detail VARCHAR
);
