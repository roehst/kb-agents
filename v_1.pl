% Knowledge base to diagnose a production service returning 500 for every request.
% Main predicate: diagnose(Observations, Diagnoses).
% - Observations is a list of atoms (signals), e.g.:
%   [service_returns_500_all_requests, recent_deploy, db_connection_refused, ...]
% - Diagnoses is a list of diag(Cause, Score, Evidence, Actions) sorted by descending Score.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Helpers
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

has(Obs, Item) :-
    memberchk(Item, Obs).

push_if_has(Obs, Item, EvIn, EvOut) :-
    ( has(Obs, Item) -> append(EvIn, [Item], EvOut)
    ; EvOut = EvIn
    ).

sort_diags(DiagsIn, DiagsOut) :-
    % Sort by descending Score using a negated key
    findall(key(-S, C, Ev, A)-diag(C, S, Ev, A), member(diag(C, S, Ev, A), DiagsIn), Pairs),
    keysort(Pairs, SortedPairs),
    findall(D, member(_-D, SortedPairs), DiagsOut).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Scoring rules: score_cause(Observations, Cause, Score, Evidence)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Dependency outage: Database
score_cause(Obs, dependency_outage(db), Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    ( has(Obs, db_down)                -> Base = 100, EDb = db_down
    ; has(Obs, db_connection_refused) -> Base = 95,  EDb = db_connection_refused
    ; has(Obs, db_timeouts)           -> Base = 85,  EDb = db_timeouts
    ),
    ( has(Obs, health_check_failing) -> Extra = 3 ; Extra = 0 ),
    Score is Base + Extra,
    Ev0 = [service_returns_500_all_requests, EDb],
    push_if_has(Obs, health_check_failing, Ev0, Ev1),
    push_if_has(Obs, no_recent_deploy,     Ev1, Evidence).

% Bad deploy or misconfiguration
score_cause(Obs, bad_deploy_misconfiguration, Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    has(Obs, recent_deploy),
    ( has(Obs, config_error_in_logs)      -> Base = 95,  E = config_error_in_logs
    ; has(Obs, missing_env_var)           -> Base = 92,  E = missing_env_var
    ; has(Obs, runtime_exceptions_in_logs)-> Base = 85,  E = runtime_exceptions_in_logs
    ;                                       Base = 40,  E = none_specific
    ),
    Score is Base,
    ( E == none_specific -> Evidence = [service_returns_500_all_requests, recent_deploy]
    ;                       Evidence = [service_returns_500_all_requests, recent_deploy, E]
    ).

% DB schema mismatch after deploy
score_cause(Obs, db_schema_mismatch_after_deploy, Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    has(Obs, recent_deploy),
    ( has(Obs, db_errors_schema_mismatch) -> Base = 98, E = db_errors_schema_mismatch
    ; has(Obs, migration_not_applied)     -> Base = 96, E = migration_not_applied
    ),
    Score is Base,
    Evidence = [service_returns_500_all_requests, recent_deploy, E].

% Disk full
score_cause(Obs, disk_full, Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    ( has(Obs, disk_full) -> Base = 92, E = disk_full
    ; has(Obs, no_space_left_on_device_in_logs) -> Base = 90, E = no_space_left_on_device_in_logs
    ),
    Score is Base,
    Evidence = [service_returns_500_all_requests, E].

% Memory exhaustion / OOM kills
score_cause(Obs, memory_exhaustion, Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    ( has(Obs, oom_kills_detected) -> Base = 90, E = oom_kills_detected
    ; has(Obs, memory_exhausted)   -> Base = 85, E = memory_exhausted
    ),
    Score is Base,
    Evidence = [service_returns_500_all_requests, E].

% Thread or connection pool exhaustion
score_cause(Obs, pool_exhaustion, Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    ( has(Obs, thread_pool_saturated)     -> Base = 82, E = thread_pool_saturated
    ; has(Obs, connection_pool_exhausted) -> Base = 80, E = connection_pool_exhausted
    ),
    Score is Base,
    Evidence = [service_returns_500_all_requests, E].

% Reverse proxy / gateway misconfiguration causing blanket 500s
score_cause(Obs, reverse_proxy_misconfiguration, Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    has(Obs, proxy_errors_500),
    has(Obs, app_healthy),
    Score = 88,
    Evidence = [service_returns_500_all_requests, proxy_errors_500, app_healthy].

% Generic triage always present when blanket 500 observed
score_cause(Obs, generic_triage, Score, Evidence) :-
    has(Obs, service_returns_500_all_requests),
    Score = 10,
    Evidence = [service_returns_500_all_requests].

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Actions for each cause
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

actions_for(dependency_outage(db), [
    verify_db_reachable_from_service,
    check_db_credentials_and_connection_string,
    check_db_status_and_replication,
    mitigate_by_failing_over_or_scaling_db,
    temporarily_reduce_traffic_or_enable_read_only_mode_if_supported
]).

actions_for(bad_deploy_misconfiguration, [
    rollback_or_fix_deploy,
    validate_env_vars_and_secrets,
    compare_config_with_last_known_good,
    run_smoke_tests_before_reenabling_traffic
]).

actions_for(db_schema_mismatch_after_deploy, [
    rollback_or_apply_missing_migrations,
    ensure_app_and_db_versions_are_compatible,
    add_migration_checks_to_ci
]).

actions_for(disk_full, [
    free_disk_space_or_extend_volume,
    rotate_or_truncate_logs,
    verify_temp_dirs_and_storage_paths,
    add_disk_alerts_and_limits
]).

actions_for(memory_exhaustion, [
    increase_memory_or_reduce_load,
    fix_memory_leaks,
    tune_heap_and_gc_settings,
    add_autoscaling_and_memory_alerts
]).

actions_for(pool_exhaustion, [
    increase_pool_sizes_with_bounds,
    fix_leaks_or_long_running_operations,
    add_timeouts_and_backpressure,
    profile_and_optimize_hot_paths
]).

actions_for(reverse_proxy_misconfiguration, [
    review_proxy_and_routing_rules,
    validate_upstream_routes_and_timeouts,
    test_canary_route_to_app_directly,
    rollback_proxy_config_change
]).

actions_for(generic_triage, [
    check_health_endpoint_and_status_pages,
    inspect_application_and_proxy_logs,
    check_recent_deployments_and_feature_flag_changes,
    verify_downstream_dependencies_and_network,
    check_database_connectivity,
    check_disk_usage_memory_cpu,
    verify_gateway_or_load_balancer_configuration,
    consider_rollback_or_disable_new_features
]).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Main predicate
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

diagnose(Observations, Diagnoses) :-
    ( has(Observations, service_returns_500_all_requests) ->
        findall(diag(Cause, Score, Evidence, Actions),
                ( score_cause(Observations, Cause, Score, Evidence),
                  actions_for(Cause, Actions)
                ),
                RawDiags),
        sort_diags(RawDiags, Diagnoses)
    ; Diagnoses = []
    ).
