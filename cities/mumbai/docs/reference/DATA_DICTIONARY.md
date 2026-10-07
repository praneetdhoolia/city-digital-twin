# Data dictionary

Auto-generated from the produced files by `src/build/build_data_dictionary.py`.
Column types are inferred from the first 400 rows. Schema letters refer to
Appendix A of the proposal.

## A1/A6 network

### `data/processed/network/cr_harbour_adjacent_station_topology.csv`

90 rows, 8 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `from_station_key` | str | CR_HB_LABEL:andheri | 90/90 |
| `to_station_key` | str | CR_HB_LABEL:jogeshwari | 90/90 |
| `timetable_service_count` | int | 56 | 90/90 |
| `from_native_boarding_nodes` | str | ["1646774124","1646774126","164... | 90/90 |
| `to_native_boarding_nodes` | str | ["7817967700","7817967701","781... | 90/90 |
| `shared_undirected_components` | str | ["10008240050"] | 90/90 |
| `status` | str | potentially_connected_undirected | 90/90 |
| `validation_scope` | str | necessary_topology_check_only_n... | 90/90 |

### `data/processed/network/cr_harbour_boarding_nodes.csv`

183 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | derived_native_boarding_candidate | 183/183 |
| `osm_node_id` | int | 213030694 | 183/183 |
| `station_keys` | str | ["CR_HB_LABEL:goregaon"] | 183/183 |
| `evidence_references` | str | {"CR_HB_LABEL:goregaon":[{"basi... | 183/183 |
| `latitude_deg` | float | 19.1648571 | 183/183 |
| `longitude_deg` | float | 72.8494067 | 183/183 |
| `native_node_tags_json` | str | {"name":"Goregaon","public_tran... | 183/183 |
| `native_presence` | str | present | 183/183 |
| `rail_parent_ways` | str | ["807592601","991001175"] | 183/183 |
| `undirected_rail_component` | int | 10008240050 | 183/183 |
| `source_native_sha256` | str | a7865ea1b59589c9202dd59711f5765... | 183/183 |
| `assignment_status` | str | candidate_only_direction_and_pl... | 183/183 |

### `data/processed/network/cr_harbour_composite_path_segments.csv`

388 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `candidate_id` | str | 96bcc9558b10d4a56225617819aa2a7... | 388/388 |
| `pattern_id` | str | e7a933b3e2d0359793b66cbdbc99855... | 388/388 |
| `leg_sequence` | int | 1 | 388/388 |
| `path_segment_sequence` | int | 1 | 388/388 |
| `osm_way_id` | int | 659490441 | 388/388 |
| `native_segment_index_zero_based` | int | 1 | 388/388 |
| `from_osm_node_id` | int | 1647133382 | 388/388 |
| `to_osm_node_id` | int | 1647133412 | 388/388 |
| `traversal_relative_to_native_order` | str | forward | 388/388 |
| `length_geodesic_m` | float | 96.65976882244685 | 388/388 |
| `direction_status` | str | missing_direction_unresolved | 388/388 |
| `against_preferred_direction` | str | False | 388/388 |
| `source_way_tags_json` | str | {"electrified":"contact_line","... | 388/388 |
| `source_route_segment_references_json` | str | [{"osm_route_relation_id":"1151... | 388/388 |

### `data/processed/network/cr_harbour_constrained_path_segments.csv`

9380 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `candidate_id` | str | cb0fd2aa6fdb62a122fa01df45977da... | 401/401 |
| `pattern_id` | str | 05e91588bca4edf87f007c0968df634... | 401/401 |
| `leg_sequence` | int | 1 | 401/401 |
| `path_segment_sequence` | int | 1 | 401/401 |
| `osm_route_relation_id` | int | 8130328 | 401/401 |
| `route_segment_index_zero_based` | int | 0 | 401/401 |
| `source_member_order` | int | 63 | 401/401 |
| `osm_way_id` | int | 207555573 | 401/401 |
| `native_segment_index_zero_based` | int | 0 | 401/401 |
| `from_osm_node_id` | int | 316306549 | 401/401 |
| `to_osm_node_id` | int | 2175054160 | 401/401 |
| `traversal_relative_to_native_order` | str | forward | 401/401 |
| `length_geodesic_m` | float | 172.21976590090844 | 401/401 |
| `direction_status` | str | missing_direction_unresolved | 401/401 |
| `against_preferred_direction` | str | False | 401/401 |
| `source_way_tags_json` | str | {"IR:zone":"CR:CSMT","covered":... | 401/401 |

### `data/processed/network/cr_harbour_mapped_route_segments.csv`

11701 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `osm_route_relation_id` | int | 8130328 | 401/401 |
| `route_segment_index_zero_based` | int | 0 | 401/401 |
| `source_member_order` | int | 63 | 401/401 |
| `osm_way_id` | int | 207555573 | 401/401 |
| `native_segment_index_zero_based` | int | 0 | 401/401 |
| `from_osm_node_id` | int | 316306549 | 401/401 |
| `to_osm_node_id` | int | 2175054160 | 401/401 |
| `traversal_relative_to_native_order` | str | forward | 401/401 |
| `length_geodesic_m` | float | 172.21976590090844 | 401/401 |
| `direction_status` | str | missing_direction_unresolved | 401/401 |
| `against_preferred_direction` | str | False | 401/401 |
| `source_way_tags_json` | str | {"IR:zone":"CR:CSMT","covered":... | 401/401 |

### `data/processed/network/cr_harbour_path_segments.csv`

22348 rows, 20 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `pattern_id` | str | 05e91588bca4edf87f007c0968df634... | 401/401 |
| `variant` | str | geometry_only | 401/401 |
| `leg_sequence` | int | 1 | 401/401 |
| `path_segment_sequence` | int | 1 | 401/401 |
| `osm_way_id` | int | 1315478119 | 401/401 |
| `native_segment_index_zero_based` | int | 0 | 401/401 |
| `from_osm_node_id` | int | 2166817451 | 401/401 |
| `to_osm_node_id` | int | 12176277916 | 401/401 |
| `traversal_relative_to_native_order` | str | forward | 401/401 |
| `length_geodesic_m` | float | 210.8357412645188 | 401/401 |
| `direction_status` | str | missing_direction_unresolved | 401/401 |
| `oneway_as_tag` | str | yes | 316/401 |
| `preferred_direction_as_tag` | str | forward | 64/401 |
| `against_preferred_direction` | str | False | 401/401 |
| `bidirectional_as_tag` | empty |  | 0/401 |
| `gauge_as_tag` | int | 1676 | 401/401 |
| `service_as_tag` | str | crossover | 8/401 |
| `usage_as_tag` | str | main | 357/401 |
| `maxspeed_as_tag` | empty |  | 0/401 |
| `directional_maxspeed_as_tag` | empty |  | 0/401 |

### `data/processed/network/cr_harbour_track_memberships.csv`

222 rows, 13 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | native_osm_way_node_membership | 222/222 |
| `osm_node_id` | int | 213030694 | 222/222 |
| `station_keys` | str | ["CR_HB_LABEL:goregaon"] | 222/222 |
| `osm_way_id` | int | 807592601 | 222/222 |
| `way_node_index_zero_based` | int | 3 | 222/222 |
| `previous_node_id` | int | 1779829758 | 183/222 |
| `next_node_id` | int | 1779829773 | 183/222 |
| `railway_tag` | str | rail | 222/222 |
| `oneway_as_tag` | str | reversible | 66/222 |
| `gauge_as_tag` | int | 1676 | 222/222 |
| `all_way_tags_json` | str | {"date:quadrupled":"1926-03-05"... | 222/222 |
| `source_native_sha256` | str | a7865ea1b59589c9202dd59711f5765... | 222/222 |
| `allocation_status` | str | track_membership_only_no_servic... | 222/222 |

### `data/processed/network/osm_access_class_evidence.csv`

2988 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `access_profile_sha256` | str | 00b1bab3857fec8dffb19cfa981a39b... | 401/401 |
| `referenced_ways_count` | int | 1 | 401/401 |
| `transport_class` | str | auto_rickshaw | 401/401 |
| `inheritance_chain` | str | ["access","vehicle","motor_vehi... | 401/401 |
| `baseline_source_key` | str | motor_vehicle | 346/401 |
| `baseline_raw_value` | str | no | 346/401 |
| `baseline_interpretation` | str | tagged_prohibition | 401/401 |
| `contributing_tags` | str | [{"key":"access","value":"permi... | 401/401 |
| `qualified_tags` | str | {} | 401/401 |
| `scope_warnings` | str | [] | 401/401 |
| `resolution_status` | str | tagged_prohibition | 401/401 |
| `simulation_permission_established` | str | False | 401/401 |

### `data/processed/network/osm_way_access_profiles.csv`

232856 rows, 2 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `osm_way_id` | int | 8458446 | 401/401 |
| `access_profile_sha256` | str | 44136fa355b3678a1146ad16f7e8649... | 401/401 |

### `data/processed/network/osm_way_attributes.csv`

232856 rows, 29 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `osm_way_id` | int | 8458446 | 401/401 |
| `highway` | str | primary | 401/401 |
| `source_path` | str | networks/osm/network_source.osm.gz | 401/401 |
| `source_sha256` | str | a7865ea1b59589c9202dd59711f5765... | 401/401 |
| `oneway_direction` | str | forward | 401/401 |
| `oneway_basis` | str | explicit | 401/401 |
| `lanes_total_count` | int | 2 | 58/401 |
| `lanes_tagged_forward_count` | empty |  | 0/401 |
| `lanes_tagged_backward_count` | empty |  | 0/401 |
| `lanes_shared_count` | empty |  | 0/401 |
| `lanes_resolved_forward_count` | int | 2 | 52/401 |
| `lanes_resolved_backward_count` | int | 0 | 52/401 |
| `lanes_status` | str | missing | 401/401 |
| `lanes_problems` | empty |  | 0/401 |
| `lane_or_direction_qualifier_keys` | str | oneway:bicycle | 1/401 |
| `speed_limit_forward_kmh` | int | 30.0 | 30/401 |
| `speed_limit_forward_source_key` | str | maxspeed | 30/401 |
| `speed_limit_forward_status` | str | missing | 401/401 |
| `speed_limit_backward_kmh` | int | 30.0 | 30/401 |
| `speed_limit_backward_source_key` | str | maxspeed | 30/401 |
| `speed_limit_backward_status` | str | missing | 401/401 |
| `width_m` | empty |  | 0/401 |
| `width_status` | str | missing | 401/401 |
| `carriageway_width_m` | empty |  | 0/401 |
| `carriageway_width_status` | str | missing | 401/401 |
| `source_tags_json` | str | {"highway":"primary","name":"Ka... | 401/401 |
| `unresolved_speed_qualifier_keys` | str | maxspeed:hgv | 18/401 |
| `source` | str | derived_from_mapper_reported_tags | 401/401 |
| `model_input_status` | str | requires_access_capacity_and_so... | 401/401 |

### `data/processed/network/road_rail_shared_nodes.csv`

1512 rows, 10 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `osm_node_id` | int | 30520639 | 401/401 |
| `longitude_deg` | float | 72.7956189 | 401/401 |
| `latitude_deg` | float | 19.6076217 | 401/401 |
| `projected_x_m` | float | 268799.74848958553 | 401/401 |
| `projected_y_m` | float | 2169554.6957416837 | 401/401 |
| `projected_crs` | str | EPSG:32643 | 401/401 |
| `source_tags_json` | str | {"railway":"level_crossing"} | 401/401 |
| `road_parent_ways_json` | str | [{"feature_value":"unclassified... | 401/401 |
| `rail_parent_ways_json` | str | [{"feature_value":"rail","geome... | 401/401 |
| `model_connection_status` | str | native_shared_node_not_transfer... | 401/401 |

## Zones

### `data/processed/zones/mmr_extent.csv`

4813 rows, 10 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `geography_id` | str | 27:519:99999:802794:0101:000000 | 401/401 |
| `district_code` | int | 519 | 401/401 |
| `subdistrict_code` | int | 99999 | 401/401 |
| `level` | str | WARD | 401/401 |
| `name` | str | Greater Mumbai (M Corp.) (Part)... | 401/401 |
| `tier` | str | core | 401/401 |
| `rule` | str | greater_mumbai | 401/401 |
| `evidence` | str | Census 2011 district 519 | 401/401 |
| `persons_count` | int | 92528 | 401/401 |
| `households_count` | int | 21985 | 401/401 |

## Observed

### `data/processed/observed/best_depot_listing.csv`

27 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | official_undated_operator_listing | 27/27 |
| `source_id` | str | best_depots_20260919 | 27/27 |
| `source_sha256` | str | 1a83a5e342232dd5d6e2863d0c8f793... | 27/27 |
| `source_row_serial` | int | 1 | 27/27 |
| `depot_code` | str | C | 27/27 |
| `depot_name` | str | Colaba | 27/27 |
| `zone_raw` | str | City Zone | 27/27 |
| `status` | str | current_operation_and_geocoding... | 27/27 |
| `address_raw` | str | Electric House, Colaba, Mumbai | 27/27 |
| `routes_raw` | str | 2L, 6Lroute1, 6Lroute2, 22L, 44... | 27/27 |
| `bus_stations_raw` | str | Colaba Depot, Chht. Shivaji Ter... | 27/27 |
| `major_operation_raw` | str | Colaba, Chht. Shivaji Terminus,... | 27/27 |

### `data/processed/observed/best_depot_route_listing.csv`

495 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | official_undated_operator_listing | 401/401 |
| `source_id` | str | best_depots_20260919 | 401/401 |
| `source_sha256` | str | 1a83a5e342232dd5d6e2863d0c8f793... | 401/401 |
| `source_row_serial` | int | 1 | 401/401 |
| `depot_code` | str | C | 401/401 |
| `depot_name` | str | Colaba | 401/401 |
| `zone_raw` | str | City Zone | 401/401 |
| `status` | str | current_operation_and_geocoding... | 401/401 |
| `route_ordinal` | int | 1 | 401/401 |
| `route_label_raw` | str | 2L | 401/401 |
| `mode` | str | bus | 401/401 |
| `identity_crosswalk_status` | str | unresolved | 401/401 |

### `data/processed/observed/best_published_fares.csv`

40 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `stage_distance_as_printed_km` | int | 5 | 40/40 |
| `fare_class` | str | non_ac_adult | 40/40 |
| `base_fare_inr` | int | 10 | 40/40 |
| `source_page_1_based` | int | 1 | 40/40 |
| `source` | str | official_fare_table_visual_tran... | 40/40 |
| `source_id` | str | best_bus_pass_2025 | 40/40 |
| `source_sha256` | str | b59d8697af65dc34ac5b3e5558c6c5c... | 40/40 |
| `transcription_sha256` | str | b9d63f17d0897a8a90a6e3f927a5b1a... | 40/40 |
| `effective_date_as_printed` | str | 2025-05-08 | 40/40 |
| `status` | str | published_table_transcribed_not... | 40/40 |
| `model_ready` | str | False | 40/40 |

### `data/processed/observed/best_published_passes.csv`

48 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `product` | str | weekly_14_trips_7_days | 48/48 |
| `up_to_distance_km` | int | 5 | 40/48 |
| `valid_days` | int | 7 | 45/48 |
| `valid_period_raw` | str | weekly | 43/48 |
| `trips` | int | 14 | 43/48 |
| `unlimited` | str | False | 45/48 |
| `price_inr` | int | 140 | 48/48 |
| `eligibility_raw` | str | Separate product eligibility an... | 48/48 |
| `source_page_1_based` | int | 2 | 48/48 |
| `source` | str | official_fare_table_visual_tran... | 48/48 |
| `source_id` | str | best_bus_pass_2025 | 48/48 |
| `source_sha256` | str | b59d8697af65dc34ac5b3e5558c6c5c... | 48/48 |
| `transcription_sha256` | str | b9d63f17d0897a8a90a6e3f927a5b1a... | 48/48 |
| `effective_date_as_printed` | str | 2025-05-08 | 48/48 |
| `status` | str | published_table_transcribed_not... | 48/48 |
| `model_ready` | str | False | 48/48 |

### `data/processed/observed/bmc_2021_signal_junctions.csv`

70 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | published_tender_inventory | 70/70 |
| `source_id` | str | bmc_signal_upgrade_spec_2021 | 70/70 |
| `source_sha256` | str | 643aa77e2d77ab6fb05c1d3edca5acf... | 70/70 |
| `source_pdf_page` | int | 63 | 70/70 |
| `source_serial` | int | 1 | 70/70 |
| `junction_name_as_printed` | str | President Hotel | 70/70 |
| `junction_type_as_printed` | str | 3-arm | 70/70 |
| `latitude_dms_as_printed` | str | 18°54'51.32"N, | 70/70 |
| `longitude_dms_as_printed` | str | 72°49'17.94"E | 70/70 |
| `latitude_degrees` | float | 18.91425555555555555555555556 | 70/70 |
| `longitude_degrees` | float | 72.82165000000000000000000000 | 70/70 |
| `coordinate_datum` | str | not_stated_in_table | 70/70 |
| `coordinate_derivation` | str | degrees + minutes/60 + seconds/... | 70/70 |
| `evidence_scope` | str | 70_junction_upgrade_tender_not_... | 70/70 |
| `operating_plan_status` | str | cycles_splits_offsets_and_phase... | 70/70 |
| `model_binding_status` | str | unmatched_reference_point_not_a... | 70/70 |

### `data/processed/observed/bmc_population_estimates.csv`

112 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | bmc_civic_diary_2025 | 112/112 |
| `source_sha256` | str | 5984b3bbde3390c2d10fe48b1cad17b... | 112/112 |
| `source_page_1_based` | int | 78 | 112/112 |
| `reference_year_as_printed` | int | 2023 | 112/112 |
| `area_name` | str | A | 112/112 |
| `geography_level` | str | administrative_ward | 112/112 |
| `region` | str | City | 112/112 |
| `population_persons_count` | int | 193520 | 112/112 |
| `area_km2` | float | 11.20 | 56/112 |
| `source` | str | published_municipal_estimate | 112/112 |
| `status` | str | source_conflicts_and_current_ge... | 112/112 |
| `model_ready` | str | False | 112/112 |

### `data/processed/observed/bus_manufacturer_seating_claims.csv`

8 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | tata_best_bus_delivery_20210807 | 8/8 |
| `source_sha256` | str | c8bb6e464633e89abdd3faf02f1c1a0... | 8/8 |
| `source_page_1_based` | int | 1 | 8/8 |
| `source` | str | manufacturer_publication | 8/8 |
| `model_as_printed` | str | Tata electric AC bus | 8/8 |
| `length_m` | float | 9 | 7/8 |
| `seated_passengers_count` | int | 25 | 8/8 |
| `capacity_text_as_printed` | str | 25-seater | 8/8 |
| `standing_passengers_count` | empty |  | 0/8 |
| `standing_status` | str | unobtained_not_zero | 8/8 |
| `claim_context` | str | BEST order configuration descri... | 8/8 |
| `current_fleet_count` | empty |  | 0/8 |
| `route_assignment` | empty |  | 0/8 |
| `model_ready` | str | False | 8/8 |
| `status` | str | licensed_configuration_and_oper... | 8/8 |

### `data/processed/observed/census_2011_age_sex.csv`

228 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `state_code` | int | 27 | 228/228 |
| `district_code` | int | 517 | 228/228 |
| `area_name` | str | District - Thane (21) | 228/228 |
| `age_band` | str | All ages | 228/228 |
| `residence` | str | Total | 228/228 |
| `persons_count` | int | 11060148 | 228/228 |
| `male_persons_count` | int | 5865078 | 228/228 |
| `female_persons_count` | int | 5195070 | 228/228 |
| `source` | str | observed | 228/228 |
| `source_id` | str | census_c14_maharashtra | 228/228 |
| `source_sha256` | str | d460de9ab07eb4383efaded69b6e766... | 228/228 |
| `source_row` | int | 407 | 228/228 |
| `observation_year` | int | 2011 | 228/228 |
| `status` | str | historical_control_not_current_... | 228/228 |

### `data/processed/observed/census_2011_b28_commuting.csv`

1320 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `state_code` | int | 27 | 401/401 |
| `district_code` | int | 517 | 401/401 |
| `residence` | str | Total | 401/401 |
| `district_name` | str | Thane | 401/401 |
| `mode_raw` | str | All Modes | 401/401 |
| `distance_band_km_raw` | str | Total | 401/401 |
| `persons_count` | int | 3600371 | 401/401 |
| `male_persons_count` | int | 2872963 | 401/401 |
| `female_persons_count` | int | 727408 | 401/401 |
| `observation_year` | int | 2011 | 401/401 |
| `universe` | str | Other workers; residence-to-wor... | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | census_b28_maharashtra | 401/401 |
| `source_sha256` | str | 0b0b001faccad197013de65996e77c7... | 401/401 |
| `calibration_eligible` | str | false | 401/401 |

### `data/processed/observed/census_2011_household_assets.csv`

4928 rows, 27 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `state_code` | int | 27 | 401/401 |
| `district_code` | int | 517 | 401/401 |
| `subdistrict_code` | int | 00000 | 401/401 |
| `town_village_code` | int | 000000 | 401/401 |
| `ward_code` | int | 0000 | 401/401 |
| `area_name` | str | District - Thane | 401/401 |
| `residence` | str | Total | 401/401 |
| `observation_year` | int | 2011 | 401/401 |
| `universe` | str | Houselisting households excludi... | 401/401 |
| `aggregation_status` | str | Nested geographical and residen... | 401/401 |
| `households_with_bicycle_pct` | float | 16.6 | 401/401 |
| `households_with_two_wheeler_pct` | float | 20.5 | 401/401 |
| `households_with_car_jeep_van_pct` | float | 7.1 | 401/401 |
| `household_size_1_pct` | float | 4 | 401/401 |
| `household_size_2_pct` | float | 10.5 | 401/401 |
| `household_size_3_pct` | float | 17.9 | 401/401 |
| `household_size_4_pct` | float | 27.1 | 401/401 |
| `household_size_5_pct` | float | 18.2 | 401/401 |
| `household_size_6_to_8_pct` | float | 18.6 | 401/401 |
| `household_size_9_plus_pct` | float | 3.8 | 401/401 |
| `household_size_sum_minus_100_pp` | float | 0.1 | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | census_hl14_thane | 401/401 |
| `source_sha256` | str | 838c8b18ebc224f54ae8043a1adbf04... | 401/401 |
| `source_sheet` | str | Sheet1 | 401/401 |
| `source_row` | int | 8 | 401/401 |
| `status` | str | historical_control_not_current_... | 401/401 |

### `data/processed/observed/census_2011_household_sizes.csv`

1071 rows, 18 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `state_code` | int | 27 | 401/401 |
| `district_code` | int | 517 | 401/401 |
| `subdistrict_code` | int | 00000 | 401/401 |
| `town_code` | int | 000000 | 401/401 |
| `area_name` | str | District - Thane | 401/401 |
| `residence` | str | Total | 401/401 |
| `household_size_band` | str | 1 | 401/401 |
| `households_count` | int | 101726 | 401/401 |
| `all_size_households_count` | int | 2516599 | 401/401 |
| `all_size_normal_household_persons_count` | int | 10962488 | 401/401 |
| `published_mean_household_size_persons` | float | 4.4 | 401/401 |
| `universe` | str | Normal households; repeated tot... | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | census_hh1_maharashtra | 401/401 |
| `source_sha256` | str | 32cde14d5871568173eef1ab33327d8... | 401/401 |
| `source_row` | int | 691 | 401/401 |
| `observation_year` | int | 2011 | 401/401 |
| `status` | str | historical_control_not_current_... | 401/401 |

### `data/processed/observed/census_2011_leaf_controls.csv`

4813 rows, 93 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `geography_id` | str | 27:519:99999:802794:0101:000000 | 401/401 |
| `state_code` | int | 27 | 401/401 |
| `district_code` | int | 519 | 401/401 |
| `subdistrict_code` | int | 99999 | 401/401 |
| `town_village_code` | int | 802794 | 401/401 |
| `ward_code` | int | 0101 | 401/401 |
| `level` | str | WARD | 401/401 |
| `name` | str | Greater Mumbai (M Corp.) (Part)... | 401/401 |
| `rural_urban` | str | Urban | 401/401 |
| `observation_year` | int | 2011 | 401/401 |
| `households_count` | int | 21985 | 401/401 |
| `persons_count` | int | 92528 | 401/401 |
| `male_persons_count` | int | 51198 | 401/401 |
| `female_persons_count` | int | 41330 | 401/401 |
| `persons_age_0_6_count` | int | 11327 | 401/401 |
| `male_age_0_6_count` | int | 6034 | 401/401 |
| `female_age_0_6_count` | int | 5293 | 401/401 |
| `literate_persons_count` | int | 70028 | 401/401 |
| `workers_count` | int | 41142 | 401/401 |
| `main_workers_count` | int | 38942 | 401/401 |
| `main_other_workers_count` | int | 38175 | 401/401 |
| `marginal_workers_count` | int | 2200 | 401/401 |
| `marginal_other_workers_count` | int | 2078 | 401/401 |
| `non_workers_count` | int | 51386 | 401/401 |
| `male_workers_count` | int | 31698 | 401/401 |
| `female_workers_count` | int | 9444 | 401/401 |
| `male_main_workers_count` | int | 30460 | 401/401 |
| `female_main_workers_count` | int | 8482 | 401/401 |
| `male_marginal_workers_count` | int | 1238 | 401/401 |
| `female_marginal_workers_count` | int | 962 | 401/401 |
| `marginal_workers_3_to_6_months_count` | int | 1975 | 401/401 |
| `male_marginal_workers_3_to_6_months_count` | int | 1109 | 401/401 |
| `female_marginal_workers_3_to_6_months_count` | int | 866 | 401/401 |
| `marginal_workers_under_3_months_count` | int | 225 | 401/401 |
| `male_marginal_workers_under_3_months_count` | int | 129 | 401/401 |
| `female_marginal_workers_under_3_months_count` | int | 96 | 401/401 |
| `male_non_workers_count` | int | 19500 | 401/401 |
| `female_non_workers_count` | int | 31886 | 401/401 |
| `main_cultivators_count` | int | 95 | 401/401 |
| `male_main_cultivators_count` | int | 74 | 401/401 |
| `female_main_cultivators_count` | int | 21 | 401/401 |
| `main_agricultural_labourers_count` | int | 108 | 401/401 |
| `male_main_agricultural_labourers_count` | int | 88 | 401/401 |
| `female_main_agricultural_labourers_count` | int | 20 | 401/401 |
| `main_household_industry_workers_count` | int | 564 | 401/401 |
| `male_main_household_industry_workers_count` | int | 388 | 401/401 |
| `female_main_household_industry_workers_count` | int | 176 | 401/401 |
| `male_main_other_workers_count` | int | 29910 | 401/401 |
| `female_main_other_workers_count` | int | 8265 | 401/401 |
| `marginal_cultivators_count` | int | 48 | 401/401 |
| `male_marginal_cultivators_count` | int | 18 | 401/401 |
| `female_marginal_cultivators_count` | int | 30 | 401/401 |
| `marginal_agricultural_labourers_count` | int | 11 | 401/401 |
| `male_marginal_agricultural_labourers_count` | int | 7 | 401/401 |
| `female_marginal_agricultural_labourers_count` | int | 4 | 401/401 |
| `marginal_household_industry_workers_count` | int | 63 | 401/401 |
| `male_marginal_household_industry_workers_count` | int | 28 | 401/401 |
| `female_marginal_household_industry_workers_count` | int | 35 | 401/401 |
| `male_marginal_other_workers_count` | int | 1185 | 401/401 |
| `female_marginal_other_workers_count` | int | 893 | 401/401 |
| `marginal_3_to_6_months_cultivators_count` | int | 48 | 401/401 |
| `male_marginal_3_to_6_months_cultivators_count` | int | 18 | 401/401 |
| `female_marginal_3_to_6_months_cultivators_count` | int | 30 | 401/401 |
| `marginal_3_to_6_months_agricultural_labourers_count` | int | 10 | 401/401 |
| `male_marginal_3_to_6_months_agricultural_labourers_count` | int | 7 | 401/401 |
| `female_marginal_3_to_6_months_agricultural_labourers_count` | int | 3 | 401/401 |
| `marginal_3_to_6_months_household_industry_workers_count` | int | 56 | 401/401 |
| `male_marginal_3_to_6_months_household_industry_workers_count` | int | 26 | 401/401 |
| `female_marginal_3_to_6_months_household_industry_workers_count` | int | 30 | 401/401 |
| `marginal_3_to_6_months_other_workers_count` | int | 1861 | 401/401 |
| `male_marginal_3_to_6_months_other_workers_count` | int | 1058 | 401/401 |
| `female_marginal_3_to_6_months_other_workers_count` | int | 803 | 401/401 |
| `marginal_under_3_months_cultivators_count` | int | 0 | 401/401 |
| `male_marginal_under_3_months_cultivators_count` | int | 0 | 401/401 |
| `female_marginal_under_3_months_cultivators_count` | int | 0 | 401/401 |
| `marginal_under_3_months_agricultural_labourers_count` | int | 1 | 401/401 |
| `male_marginal_under_3_months_agricultural_labourers_count` | int | 0 | 401/401 |
| `female_marginal_under_3_months_agricultural_labourers_count` | int | 1 | 401/401 |
| `marginal_under_3_months_household_industry_workers_count` | int | 7 | 401/401 |
| `male_marginal_under_3_months_household_industry_workers_count` | int | 2 | 401/401 |
| `female_marginal_under_3_months_household_industry_workers_count` | int | 5 | 401/401 |
| `marginal_under_3_months_other_workers_count` | int | 217 | 401/401 |
| `male_marginal_under_3_months_other_workers_count` | int | 127 | 401/401 |
| `female_marginal_under_3_months_other_workers_count` | int | 90 | 401/401 |
| `male_literate_persons_count` | int | 40812 | 401/401 |
| `female_literate_persons_count` | int | 29216 | 401/401 |
| `illiterate_persons_count` | int | 22500 | 401/401 |
| `male_illiterate_persons_count` | int | 10386 | 401/401 |
| `female_illiterate_persons_count` | int | 12114 | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | census_mumbai_pca | 401/401 |
| `source_sha256` | str | 56e378aeda1353b23482945b38e4707... | 401/401 |
| `spatial_status` | str | Historical source district; MMR... | 401/401 |

### `data/processed/observed/census_2011_school_attendance.csv`

1536 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `state_code` | int | 27 | 401/401 |
| `district_code` | int | 517 | 401/401 |
| `area_name` | str | District-Thane | 401/401 |
| `residence` | str | Total | 401/401 |
| `age_years_or_band` | str | 5-19 | 401/401 |
| `attends_education` | str | true | 401/401 |
| `economic_activity` | str | main_worker | 401/401 |
| `persons_count` | int | 35801 | 401/401 |
| `male_persons_count` | int | 22208 | 401/401 |
| `female_persons_count` | int | 13593 | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | census_c12_maharashtra | 401/401 |
| `source_sha256` | str | 104cc65fb8b4822642cc2a36ca925ac... | 401/401 |
| `source_row` | int | 1016 | 401/401 |
| `observation_year` | int | 2011 | 401/401 |
| `status` | str | historical_control_not_current_... | 401/401 |

### `data/processed/observed/census_2011_single_year_ages.csv`

1236 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `state_code` | int | 27 | 401/401 |
| `district_code` | int | 517 | 401/401 |
| `area_name` | str | District - Thane (21) | 401/401 |
| `residence` | str | Total | 401/401 |
| `age_years_or_band` | str | All ages | 401/401 |
| `persons_count` | int | 11060148 | 401/401 |
| `male_persons_count` | int | 5865078 | 401/401 |
| `female_persons_count` | int | 5195070 | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | census_c13_maharashtra | 401/401 |
| `source_sha256` | str | 3a1e82a60ecb1363817e86a5080703f... | 401/401 |
| `source_row` | int | 2171 | 401/401 |
| `observation_year` | int | 2011 | 401/401 |
| `status` | str | historical_control_not_current_... | 401/401 |

### `data/processed/observed/census_2011_work_status.csv`

192 rows, 32 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `state_code` | int | 27 | 192/192 |
| `district_code` | int | 517 | 192/192 |
| `area_name` | str | District - Thane (21) | 192/192 |
| `residence` | str | Total | 192/192 |
| `age_band` | str | Total | 192/192 |
| `source` | str | observed | 192/192 |
| `source_id` | str | census_b01_maharashtra | 192/192 |
| `source_sha256` | str | 268c1121ac80fa24c480a20e82b7342... | 192/192 |
| `source_row` | int | 1017 | 192/192 |
| `observation_year` | int | 2011 | 192/192 |
| `status` | str | historical_control_not_current_... | 192/192 |
| `population_persons_count` | int | 11060148 | 192/192 |
| `population_male_persons_count` | int | 5865078 | 192/192 |
| `population_female_persons_count` | int | 5195070 | 192/192 |
| `main_worker_persons_count` | int | 3930511 | 192/192 |
| `main_worker_male_persons_count` | int | 3059503 | 192/192 |
| `main_worker_female_persons_count` | int | 871008 | 192/192 |
| `marginal_worker_under_3_months_persons_count` | int | 79842 | 192/192 |
| `marginal_worker_under_3_months_male_persons_count` | int | 40558 | 192/192 |
| `marginal_worker_under_3_months_female_persons_count` | int | 39284 | 192/192 |
| `marginal_worker_3_to_6_months_persons_count` | int | 482414 | 192/192 |
| `marginal_worker_3_to_6_months_male_persons_count` | int | 263062 | 192/192 |
| `marginal_worker_3_to_6_months_female_persons_count` | int | 219352 | 192/192 |
| `marginal_worker_seeking_available_persons_count` | int | 195235 | 192/192 |
| `marginal_worker_seeking_available_male_persons_count` | int | 117215 | 192/192 |
| `marginal_worker_seeking_available_female_persons_count` | int | 78020 | 192/192 |
| `non_worker_persons_count` | int | 6567381 | 192/192 |
| `non_worker_male_persons_count` | int | 2501955 | 192/192 |
| `non_worker_female_persons_count` | int | 4065426 | 192/192 |
| `non_worker_seeking_available_persons_count` | int | 319235 | 192/192 |
| `non_worker_seeking_available_male_persons_count` | int | 153859 | 192/192 |
| `non_worker_seeking_available_female_persons_count` | int | 165376 | 192/192 |

### `data/processed/observed/coastal_2016_daily_counts.csv`

51 rows, 17 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 51/51 |
| `source_id` | str | bmc_coastal_traffic_peer_review... | 51/51 |
| `source_sha256` | str | a40925dbeea1a5de2f41980cdc39299... | 51/51 |
| `survey_month` | str | 2016-01 | 51/51 |
| `count_survey_days` | int | 7 | 51/51 |
| `exact_survey_dates` | str | not_reported_in_section | 51/51 |
| `site_georeferencing` | str | unresolved | 51/51 |
| `target_status` | str | historical_selected_sites_not_c... | 51/51 |
| `source_table` | str | 4-3 | 51/51 |
| `source_pdf_pages` | str | 43;44 | 51/51 |
| `site_id` | int | 1 | 51/51 |
| `location` | str | Marine Drive (Kilachand Chowk) | 51/51 |
| `component` | str | direction_1 | 51/51 |
| `direction` | str | NCPA-Haji Ali | 51/51 |
| `adt_vehicles_per_day` | int | 30508 | 51/51 |
| `source_total_check` | str | exact | 51/51 |
| `aggregation` | str | seven_day_average_daily_traffic... | 51/51 |

### `data/processed/observed/coastal_2016_peak_counts.csv`

34 rows, 18 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 34/34 |
| `source_id` | str | bmc_coastal_traffic_peer_review... | 34/34 |
| `source_sha256` | str | a40925dbeea1a5de2f41980cdc39299... | 34/34 |
| `survey_month` | str | 2016-01 | 34/34 |
| `count_survey_days` | int | 7 | 34/34 |
| `exact_survey_dates` | str | not_reported_in_section | 34/34 |
| `site_georeferencing` | str | unresolved | 34/34 |
| `target_status` | str | historical_selected_sites_not_c... | 34/34 |
| `source_table` | str | 4-4 | 34/34 |
| `source_pdf_page` | int | 48 | 34/34 |
| `site_id` | int | 1 | 34/34 |
| `location` | str | Marine Drive (Kilachand Chowk) | 34/34 |
| `period` | str | morning | 34/34 |
| `local_start_time` | str | 10:00 | 34/34 |
| `local_end_time` | str | 11:00 | 34/34 |
| `average_peak_vehicles_per_hour` | int | 5870 | 34/34 |
| `direction_scope` | str | not_broken_out_by_direction_in_... | 34/34 |
| `aggregation` | str | average_peak_hour_not_saturatio... | 34/34 |

### `data/processed/observed/coastal_2016_peak_vehicle_shares.csv`

103 rows, 18 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 103/103 |
| `source_id` | str | bmc_coastal_traffic_peer_review... | 103/103 |
| `source_sha256` | str | a40925dbeea1a5de2f41980cdc39299... | 103/103 |
| `survey_month` | str | 2016-01 | 103/103 |
| `count_survey_days` | int | 7 | 103/103 |
| `exact_survey_dates` | str | not_reported_in_section | 103/103 |
| `site_georeferencing` | str | unresolved | 103/103 |
| `target_status` | str | historical_selected_sites_not_c... | 103/103 |
| `source_table` | str | 4-5 | 103/103 |
| `source_pdf_page` | int | 50 | 103/103 |
| `site_id` | int | 1 | 103/103 |
| `location` | str | Marine Drive (Kilachand Chowk) | 103/103 |
| `vehicle_class_as_printed` | str | Two Wheelers | 103/103 |
| `published_share_percent` | int | 12 | 103/103 |
| `published_precision_percent` | int | 1 | 103/103 |
| `zero_cell_status` | str | nonzero | 103/103 |
| `peak_and_direction_scope` | str | not_split_by_morning_evening_or... | 103/103 |
| `count_derivation_status` | str | not_multiplied_by_daily_or_peri... | 103/103 |

### `data/processed/observed/coastal_2016_travel_times.csv`

90 rows, 19 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | structural_table_cell | 90/90 |
| `source_id` | str | bmc_coastal_traffic_peer_review... | 90/90 |
| `source_sha256` | str | a40925dbeea1a5de2f41980cdc39299... | 90/90 |
| `source_pdf_page` | int | 59 | 90/90 |
| `source_printed_page` | int | 42 | 90/90 |
| `source_table` | str | 4-10 | 90/90 |
| `report_edition` | str | November 2016 | 90/90 |
| `survey_date` | str | not_stated_in_speed_delay_section | 90/90 |
| `origin_source_zone_id` | int | 1 | 90/90 |
| `destination_source_zone_id` | int | 1 | 90/90 |
| `direction` | str | North Bound | 90/90 |
| `peak_period` | str | Evening Peak | 90/90 |
| `period_clock_bounds` | str | not_stated_in_table | 90/90 |
| `travel_time_hours` | float | 0.00 | 90/90 |
| `travel_time_seconds` | int | 0.00 | 90/90 |
| `cell_status` | str | structural_diagonal_not_observe... | 90/90 |
| `mode_definition` | str | survey_vehicle_class_not_stated... | 90/90 |
| `zone_mapping_status` | str | study_zone_ids_not_georeferenced | 90/90 |
| `target_status` | str | historical_evidence_not_current... | 90/90 |

### `data/processed/observed/cr_harbour_layout_annotations.csv`

44 rows, 9 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | published_layout_annotation | 44/44 |
| `source_id` | str | cr_public_harbour_down_20260501 | 44/44 |
| `source_sha256` | str | 7774ae4aacc1d0ccf5d07ce10f557c3... | 44/44 |
| `source_page` | int | 1 | 44/44 |
| `train_number` | int | 99003 | 44/44 |
| `aligned_station_row_label` | str | Mumbai CSMT | 44/44 |
| `annotation_as_printed` | str | TNA | 44/44 |
| `source_x_pdf_pt` | float | 429.721469 | 44/44 |
| `source_y_pdf_pt` | float | 458.905226 | 44/44 |

### `data/processed/observed/cr_harbour_semantic_resolutions.csv`

59 rows, 7 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | derived_layout_interpretation | 59/59 |
| `train_number` | int | 91491 | 59/59 |
| `action` | str | station_reference_replaces_row_... | 59/59 |
| `original_cell` | str | {"aligned_station_row_label": "... | 59/59 |
| `supporting_annotation` | str | {"aligned_station_row_label": "... | 59/59 |
| `resolved_station_key` | str | CR_EXTERNAL_CODE:BVI | 56/59 |
| `corroboration` | str | printed_BVI_reference_only_bran... | 59/59 |

### `data/processed/observed/cr_holiday_date_evidence_2026.csv`

13 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | derived_name_match | 13/13 |
| `source_id` | str | cr_public_holidays_2026 | 13/13 |
| `source_sha256` | str | 22f2220419573626930e8591808a693... | 13/13 |
| `source_page` | int | 1 | 13/13 |
| `cr_rule_as_printed` | str | Republic Day    26th January. | 13/13 |
| `date_source_id` | str | maha_public_holidays_2026 | 13/13 |
| `date_source_sha256` | str | f689908ac6b414f7e241671fe5836f6... | 13/13 |
| `reference_year` | int | 2026 | 13/13 |
| `operation_rule` | str | Sunday_schedule | 13/13 |
| `application_status` | str | date_evidence_only_not_a_comple... | 13/13 |
| `matched_state_holiday` | str | Republic Day | 13/13 |
| `candidate_date` | str | 2026-01-26 | 13/13 |
| `match_status` | str | name_and_published_date_matched | 13/13 |
| `date_source_page` | int | 5 | 13/13 |

### `data/processed/observed/cr_printed_timetable_cells.csv`

35188 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | cr_public_harbour_ac_20260501 | 401/401 |
| `source_sha256` | str | f8148949f167838c6c46933dbdf6a89... | 401/401 |
| `source_page` | int | 1 | 401/401 |
| `table_band` | int | 1 | 401/401 |
| `train_number` | int | 98009 | 401/401 |
| `aligned_station_row_label` | str | Reay Road | 401/401 |
| `station_row_order` | int | 5 | 401/401 |
| `printed_local_hhmm` | str | 04:56 | 401/401 |
| `source_x_pdf_pt` | float | 207.96597 | 401/401 |
| `source_y_pdf_pt` | float | 585.806542 | 401/401 |
| `source` | str | published_timetable_cell | 401/401 |
| `validation_status` | str | station_calendar_vehicle_stoppi... | 401/401 |

### `data/processed/observed/cr_service_markers.csv`

256 rows, 20 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | published_service_marker | 162/162 |
| `source_id` | str | cr_public_harbour_ac_20260501 | 162/162 |
| `source_sha256` | str | f8148949f167838c6c46933dbdf6a89... | 162/162 |
| `source_page` | int | 1 | 162/162 |
| `train_number` | int | 98009 | 162/162 |
| `vehicle_marker_as_printed` | str | AC
 | 162/162 |
| `calendar_marker_as_printed` | str | X | 85/162 |
| `formation_cars` | int | 15 | 54/162 |
| `climate_control_as_printed` | str | AC | 162/162 |
| `excludes_saturday_by_marker` | int | 0 | 162/162 |
| `excludes_sunday_by_marker` | int | 1 | 162/162 |
| `excludes_nominated_holiday_by_marker` | int | 1 | 162/162 |
| `non_ac_substitution_days_when_running` | str | Sunday;nominated_holiday | 42/162 |
| `exclusion_precedence` | str | cancellation_precedes_rake_subs... | 162/162 |
| `calendar_legend_source_id` | str | cr_public_harbour_ac_20260501 | 162/162 |
| `calendar_legend_sha256` | str | f8148949f167838c6c46933dbdf6a89... | 162/162 |
| `source_header_x_pdf_pt` | float | 207.974229 | 162/162 |
| `effective_date_status` | str | retain_source_vintage_reconcile... | 162/162 |
| `service_identity_status` | str | supplement_overlay_not_addition... | 162/162 |
| `operational_calendar_status` | str | holiday_dates_and_complete_cale... | 162/162 |

### `data/processed/observed/district_age_population_projections.csv`

21000 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | modelled | 401/401 |
| `source_id` | str | iips_district_projections_2012_... | 401/401 |
| `source_sha256` | str | 10ee5c104402d5f9e3e5b5476b6959c... | 401/401 |
| `source_pdf_page` | int | 1041 | 401/401 |
| `reference_date_basis` | str | 01 March | 401/401 |
| `publisher_citation_year` | int | 2022 | 401/401 |
| `state_name` | str | Maharashtra | 401/401 |
| `district_name_as_printed` | str | Nandurbar | 401/401 |
| `district_number_within_report_state` | int | 01 | 401/401 |
| `boundary_year` | int | 2011 | 401/401 |
| `status` | str | published_district_projection_n... | 401/401 |
| `reference_year` | int | 2012 | 401/401 |
| `age_label` | str | All ages | 401/401 |
| `male_persons_count` | int | 849630 | 401/401 |
| `female_persons_count` | int | 830090 | 401/401 |

### `data/processed/observed/district_population_projections.csv`

175 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | modelled | 175/175 |
| `source_id` | str | iips_district_projections_2012_... | 175/175 |
| `source_sha256` | str | 10ee5c104402d5f9e3e5b5476b6959c... | 175/175 |
| `source_pdf_page` | int | 48 | 175/175 |
| `reference_date_basis` | str | 01 March | 175/175 |
| `publisher_citation_year` | int | 2022 | 175/175 |
| `state_name` | str | Maharashtra | 175/175 |
| `district_name_as_printed` | str | Nandurbar | 175/175 |
| `district_number_within_report_state` | int | 01 | 175/175 |
| `boundary_year` | int | 2011 | 175/175 |
| `status` | str | published_district_projection_n... | 175/175 |
| `reference_year` | int | 2011 | 175/175 |
| `male_persons_count` | int | 833170 | 175/175 |
| `female_persons_count` | int | 815125 | 175/175 |

### `data/processed/observed/ec6_district_controls.csv`

432 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `observation_year` | int | 2013 | 401/401 |
| `geography_level` | str | historical_district | 401/401 |
| `ec_district_code` | int | 01 | 395/401 |
| `geography_name` | str | Nandurbar | 401/401 |
| `table` | float | 2.8 | 401/401 |
| `dimension` | str | residence | 401/401 |
| `category` | str | rural | 401/401 |
| `measure` | str | establishments | 401/401 |
| `value_count` | int | 28466 | 401/401 |
| `source` | str | published_census_count | 401/401 |
| `derivation` | str | combined minus urban; rural cel... | 4/401 |
| `source_id` | str | maharashtra_ec6_final | 401/401 |
| `source_sha256` | str | e1d10089c2662f20badfdd7c517287d... | 401/401 |
| `pdf_page` | int | 35 | 401/401 |
| `status` | str | historical_control_not_current_... | 401/401 |

### `data/processed/observed/economic_survey_bus_controls.csv`

34 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 34/34 |
| `source_id` | str | maha_economic_survey_2025_26 | 34/34 |
| `source_sha256` | str | 954fceeb3803c2a79f2f50c615a7e7e... | 34/34 |
| `publication_edition` | str | 2025-26 | 34/34 |
| `status` | str | dated_published_aggregate_not_c... | 34/34 |
| `source_pdf_page` | int | 219 | 34/34 |
| `source_table` | float | 9.27 | 34/34 |
| `provider` | str | MSRTC (City operations) | 34/34 |
| `reference_date_as_printed` | str | 2024-03-31 | 34/34 |
| `averaging_period` | str | not_explicit_beyond_as_on_date_... | 34/34 |
| `average_vehicles_on_road_per_day_count` | int | 74 | 33/34 |
| `average_passengers_per_day_lakh` | float | 0.31 | 33/34 |
| `average_effective_km_per_day_lakh` | float | 0.13 | 33/34 |
| `missing_value_marker` | str | - | 34/34 |

### `data/processed/observed/economic_survey_metro_controls.csv`

6 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 6/6 |
| `source_id` | str | maha_economic_survey_2025_26 | 6/6 |
| `source_sha256` | str | 954fceeb3803c2a79f2f50c615a7e7e... | 6/6 |
| `publication_edition` | str | 2025-26 | 6/6 |
| `source_pdf_page` | int | 223 | 6/6 |
| `source_table` | float | 9.34 | 6/6 |
| `control_group_id` | str | mumbai_1 | 6/6 |
| `route_ids` | str | mumbai_1 | 6/6 |
| `route_count` | int | 1 | 6/6 |
| `average_passengers_per_day_lakh` | float | 5.00 | 6/6 |
| `averaging_period` | str | not_stated_in_table | 6/6 |
| `passenger_count_definition` | str | not_resolved_as_unique_people_j... | 6/6 |
| `allocation_status` | str | single_route_control | 6/6 |
| `target_status` | str | requires_period_and_counting_de... | 6/6 |

### `data/processed/observed/economic_survey_metro_routes.csv`

9 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 9/9 |
| `source_id` | str | maha_economic_survey_2025_26 | 9/9 |
| `source_sha256` | str | 954fceeb3803c2a79f2f50c615a7e7e... | 9/9 |
| `publication_edition` | str | 2025-26 | 9/9 |
| `source_pdf_page` | int | 223 | 9/9 |
| `source_table` | float | 9.34 | 9/9 |
| `route_id` | str | mumbai_1 | 9/9 |
| `passenger_control_group_id` | str | mumbai_1 | 9/9 |
| `route_as_printed` | str | 1 Varsova to Ghatkoper | 9/9 |
| `commissioned_month_as_printed` | str | June 2014 | 9/9 |
| `reported_length_km` | float | 11.40 | 9/9 |
| `commissioning_scope` | str | table_entry_not_complete_phase_... | 9/9 |

### `data/processed/observed/economic_survey_port_controls.csv`

4 rows, 19 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 4/4 |
| `source_id` | str | maha_economic_survey_2025_26 | 4/4 |
| `source_sha256` | str | 954fceeb3803c2a79f2f50c615a7e7e... | 4/4 |
| `publication_edition` | str | 2025-26 | 4/4 |
| `source_pdf_page` | int | 225 | 4/4 |
| `source_table` | float | 9.36 | 4/4 |
| `port` | str | Mumbai Port | 4/4 |
| `reference_financial_year` | str | 2023-24 | 4/4 |
| `cargo_capacity_lakh_mt` | float | 838.50 | 4/4 |
| `cargo_handled_lakh_mt` | float | 672.60 | 4/4 |
| `import_lakh_mt` | float | 490.26 | 4/4 |
| `export_lakh_mt` | float | 182.34 | 4/4 |
| `passengers_handled_thousands` | float | 277.90 | 2/4 |
| `vessels_handled_count` | int | 7519 | 4/4 |
| `passengers_cell_status` | str | reported | 4/4 |
| `cargo_unit_as_printed` | str | lakh MT | 4/4 |
| `cargo_mode_split` | str | not_supplied_in_table | 4/4 |
| `passenger_count_scope` | str | port_handled_traffic_not_establ... | 4/4 |
| `target_status` | str | requires_modal_scope_and_period... | 4/4 |

### `data/processed/observed/economic_survey_suburban_rail_controls.csv`

1 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 1/1 |
| `source_id` | str | maha_economic_survey_2025_26 | 1/1 |
| `source_sha256` | str | 954fceeb3803c2a79f2f50c615a7e7e... | 1/1 |
| `publication_edition` | str | 2025-26 | 1/1 |
| `status` | str | dated_published_aggregate_not_c... | 1/1 |
| `source_pdf_page` | int | 221 | 1/1 |
| `source_section` | float | 9.29 | 1/1 |
| `service_universe` | str | Mumbai suburban Western and Cen... | 1/1 |
| `reference_financial_year` | str | 2024-25 | 1/1 |
| `daily_fleet_local_trains_count` | int | 238 | 1/1 |
| `of_which_ac_local_trains_count` | int | 13 | 1/1 |
| `train_services_count` | int | 3104 | 1/1 |
| `of_which_ac_services_count` | int | 175 | 1/1 |
| `average_passengers_per_day_lakh` | float | 75.9 | 1/1 |
| `passenger_count_definition` | str | not_resolved_as_unique_people_j... | 1/1 |

### `data/processed/observed/jnpa_rake_observations.csv`

39 rows, 17 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | jnpa_daily_icd_20260317 | 39/39 |
| `source_sha256` | str | b9e7cbbcf335c91e5b5fae224a728bd... | 39/39 |
| `source_page` | int | 2 | 39/39 |
| `handled_date` | str | 2026-03-16 | 39/39 |
| `rake_id` | str | R256820 | 39/39 |
| `arrival_local_raw` | str | 14-Mar-2026 18:00 | 39/39 |
| `completion_local_raw` | str | 16-Mar-2026 21:40 | 39/39 |
| `departure_local_raw` | str | 16-Mar-2026 19:30 | 36/39 |
| `export_discharged_teu_count` | int | 90 | 39/39 |
| `import_loaded_teu_count` | int | 90 | 39/39 |
| `cargo_subtotals_agree` | str | True | 39/39 |
| `timestamp_order_agrees` | str | True | 39/39 |
| `arrival_to_completion_minutes` | int | 3100.0 | 39/39 |
| `arrival_to_departure_minutes` | int | 1095.0 | 36/39 |
| `prefix_on_rake_line_raw` | str | 1   R256820   T1-N CONR       B... | 39/39 |
| `source` | str | operator_reported_handled_rake | 39/39 |
| `validation_status` | str | source_totals_checked_route_clo... | 39/39 |

### `data/processed/observed/jvlr_journal_classified_counts.csv`

18 rows, 27 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 18/18 |
| `source_id` | str | jvlr_traffic_study_2026_pdf | 18/18 |
| `source_sha256` | str | 0a14ac9a0c70e4b08a760644c82cdc0... | 18/18 |
| `survey_date` | str | 2025-06-24 | 18/18 |
| `survey_start_date` | str | 2025-06-23 | 18/18 |
| `survey_end_date` | str | 2025-06-29 | 18/18 |
| `time_basis` | str | published_local_clock_times_no_... | 18/18 |
| `day_selection` | str | highest_aggregate_volume_day_in... | 18/18 |
| `calibration_status` | str | requires_2025_scenario_and_coun... | 18/18 |
| `source_pdf_page` | int | 8 | 18/18 |
| `source_table` | int | 3 | 18/18 |
| `row_id` | float | 1.1 | 18/18 |
| `site` | str | Arterial Links Passing Through ... | 18/18 |
| `road_label` | str | Road 1, Westbound (towards Powai) | 18/18 |
| `peak_start_time` | str | 09:15:00 | 18/18 |
| `peak_end_time` | str | 10:15:00 | 18/18 |
| `cars_vehicles_h` | int | 420 | 18/18 |
| `two_wheelers_vehicles_h` | int | 1140 | 18/18 |
| `auto_vehicles_h` | int | 750 | 18/18 |
| `truck_vehicles_h` | int | 12 | 18/18 |
| `tempo_vehicles_h` | int | 36 | 18/18 |
| `bus_vehicles_h` | int | 78 | 18/18 |
| `cycle_vehicles_h` | int | 0 | 18/18 |
| `pedestrians_persons_h` | int | 42 | 18/18 |
| `published_flow_pcu_h` | int | 2046 | 18/18 |
| `observation_duration_s` | int | 3600 | 18/18 |
| `pcu_flow_source` | str | derived_from_classified_counts_... | 18/18 |

### `data/processed/observed/jvlr_journal_pcu_factors.csv`

7 rows, 9 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | literature | 7/7 |
| `source_id` | str | jvlr_traffic_study_2026_pdf | 7/7 |
| `source_sha256` | str | 0a14ac9a0c70e4b08a760644c82cdc0... | 7/7 |
| `source_pdf_page` | int | 4 | 7/7 |
| `source_table` | int | 1 | 7/7 |
| `source_row` | int | 1 | 7/7 |
| `vehicle_categories` | str | Passenger car, tempo, auto, jee... | 7/7 |
| `pcu_equivalency_factor` | float | 1.0 | 7/7 |
| `purpose` | str | reproduce_published_count_conve... | 7/7 |

### `data/processed/observed/jvlr_journal_road_controls.csv`

18 rows, 24 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | literature | 18/18 |
| `source_id` | str | jvlr_traffic_study_2026_pdf | 18/18 |
| `source_sha256` | str | 0a14ac9a0c70e4b08a760644c82cdc0... | 18/18 |
| `survey_date` | str | 2025-06-24 | 18/18 |
| `survey_start_date` | str | 2025-06-23 | 18/18 |
| `survey_end_date` | str | 2025-06-29 | 18/18 |
| `time_basis` | str | published_local_clock_times_no_... | 18/18 |
| `day_selection` | str | highest_aggregate_volume_day_in... | 18/18 |
| `calibration_status` | str | requires_2025_scenario_and_coun... | 18/18 |
| `source_pdf_page` | int | 11 | 18/18 |
| `source_table` | int | 4 | 18/18 |
| `row_id` | float | 1.1 | 18/18 |
| `site` | str | Arterial Links Passing Through ... | 18/18 |
| `road_label` | str | Road 1, Westbound (towards Powai) | 18/18 |
| `speed_source` | str | official_reference_limit_report... | 18/18 |
| `density_source` | str | flow_divided_by_reference_limit... | 18/18 |
| `lanes_count` | int | 2 | 18/18 |
| `official_reference_speed_kmh` | int | 70 | 18/18 |
| `published_flow_pcu_h` | int | 2046 | 18/18 |
| `flow_pcu_h_lane` | float | 1023 | 18/18 |
| `los_flow` | str | B | 18/18 |
| `indicative_density_pcu_km` | float | 29.23 | 18/18 |
| `indicative_density_pcu_km_lane` | float | 14.62 | 18/18 |
| `los_density` | str | C | 18/18 |

### `data/processed/observed/jvlr_journal_road_inventory.csv`

18 rows, 29 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 18/18 |
| `source_id` | str | jvlr_traffic_study_2026_pdf | 18/18 |
| `source_sha256` | str | 0a14ac9a0c70e4b08a760644c82cdc0... | 18/18 |
| `source_pdf_page` | int | 15 | 18/18 |
| `source_table` | int | 6 | 18/18 |
| `row_id` | float | 1.1 | 18/18 |
| `site` | str | Arterial Links Passing Through ... | 18/18 |
| `road_label` | str | Road 1, Westbound (towards Powai) | 18/18 |
| `survey_start_date` | str | 2025-06-23 | 18/18 |
| `survey_end_date` | str | 2025-06-29 | 18/18 |
| `lane_marking_reported` | str | ✅ | 18/18 |
| `shoulders_reported` | str | ❌ | 18/18 |
| `median_reported` | str | ✅ | 18/18 |
| `parking_reported` | str | ❌ | 18/18 |
| `service_lane_reported` | str | ❌ | 18/18 |
| `bicycle_facility_reported` | str | ❌ | 18/18 |
| `pedestrian_pathway_reported` | str | ✅ (2 m) | 18/18 |
| `zebra_crossing_reported` | str | ❌ | 18/18 |
| `vending_zones_reported` | str | ❌ | 18/18 |
| `utility_corridor_reported` | str | ✅ | 18/18 |
| `plantation_reported` | str | ✅ | 18/18 |
| `street_hardware_reported` | str | signals | 18/18 |
| `additional_land_reported` | str | ❌ | 18/18 |
| `exclusive_row_reported` | str | 45 m | 18/18 |
| `median_reported_width_m` | float | 4.5 | 2/18 |
| `service_lane_reported_width_m` | int | 5 | 2/18 |
| `pedestrian_pathway_reported_width_m` | float | 2 | 15/18 |
| `exclusive_right_of_way_width_m` | int | 45 | 18/18 |
| `model_assignment_status` | str | unassigned_requires_location_an... | 18/18 |

### `data/processed/observed/jvlr_journal_temporal_variability.csv`

18 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | derived | 18/18 |
| `source_id` | str | jvlr_traffic_study_2026_pdf | 18/18 |
| `source_sha256` | str | 0a14ac9a0c70e4b08a760644c82cdc0... | 18/18 |
| `source_pdf_page` | int | 12 | 18/18 |
| `source_table` | int | 5 | 18/18 |
| `row_id` | float | 1.1 | 18/18 |
| `site` | str | Arterial Links Passing Through ... | 18/18 |
| `road_label` | str | Road 1, Westbound (towards Powai) | 18/18 |
| `survey_start_date` | str | 2025-06-23 | 18/18 |
| `survey_end_date` | str | 2025-06-29 | 18/18 |
| `mean_flow_pcu_h_lane` | float | 951.4 | 18/18 |
| `sd_flow_pcu_h_lane` | float | 73.2 | 18/18 |
| `coefficient_of_variation_percent` | float | 7.7 | 18/18 |
| `interpretation` | str | Low variability | 18/18 |
| `statistic_scope` | str | published_peak_period_summary_n... | 18/18 |

### `data/processed/observed/jvlr_poster_road_controls.csv`

18 rows, 22 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `row_id` | float | 1.1 | 18/18 |
| `site` | str | Gandhinagar Junction | 18/18 |
| `road_label` | str | Road 1 (towards Powai) | 18/18 |
| `lanes` | int | 2 | 18/18 |
| `speed_kmh` | int | 70 | 18/18 |
| `flow_pcu_h` | int | 2046 | 18/18 |
| `flow_pcu_h_lane` | float | 1023 | 18/18 |
| `los_flow` | str | B | 18/18 |
| `density_pcu_km` | float | 29.23 | 18/18 |
| `density_pcu_km_lane` | float | 14.62 | 18/18 |
| `los_density` | str | C | 18/18 |
| `source` | str | literature | 18/18 |
| `source_id` | str | jvlr_conference_poster_2026_res... | 18/18 |
| `source_sha256` | str | 3cd8dd8cf3e6ac4f86b1ad7ca1d5fbe... | 18/18 |
| `poster_sha256` | str | 6f85108270324e7d1dc4dd58f209c03... | 18/18 |
| `source_pdf_page` | int | 1 | 18/18 |
| `survey_date` | empty |  | 0/18 |
| `survey_time_window` | empty |  | 0/18 |
| `speed_measurement_method` | empty |  | 0/18 |
| `pcu_conversion_factors` | empty |  | 0/18 |
| `validation_status` | str | published_derived_quantities_wi... | 18/18 |
| `calibration_eligible` | str | False | 18/18 |

### `data/processed/observed/maha_holidays_2026.csv`

26 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | published_holiday | 26/26 |
| `source_id` | str | maha_public_holidays_2026 | 26/26 |
| `source_sha256` | str | f689908ac6b414f7e241671fe5836f6... | 26/26 |
| `source_page` | int | 5 | 26/26 |
| `section_scope` | str | public_holidays | 26/26 |
| `serial` | int | 1 | 26/26 |
| `holiday_name_as_printed` | str | Republic Day | 26/26 |
| `gregorian_date` | str | 2026-01-26 | 26/26 |
| `weekday_as_printed` | str | Monday | 26/26 |
| `saka_date_as_printed` | str | 6 Magh,1947 | 26/26 |
| `railway_operation_status` | str | not_established_by_state_notifi... | 26/26 |

### `data/processed/observed/mbmt_contract_capacities.csv`

3 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `configuration` | str | 12 metre electric AC | 3/3 |
| `section_start_page_1_based` | int | 189 | 3/3 |
| `source_page_1_based` | int | 194 | 3/3 |
| `seating_text_as_printed` | str | Min 36 + Driver | 3/3 |
| `seat_requirement_kind` | str | minimum | 3/3 |
| `passenger_seats_count` | int | 36 | 3/3 |
| `driver_separate` | str | True | 3/3 |
| `standing_text_as_printed` | str | Calculation as per AIS 052 | 3/3 |
| `standing_passengers_count` | empty |  | 0/3 |
| `source_id` | str | mbmt_electric_bus_agreement | 3/3 |
| `source_sha256` | str | 687ae4cce93548ea8d309f763c3fc6d... | 3/3 |
| `transcription_sha256` | str | 5a6dc3e868514c404e7221583b81c4d... | 3/3 |
| `source` | str | municipal_contract_visual_trans... | 3/3 |
| `status` | str | contract_specifications_not_ver... | 3/3 |
| `model_ready` | str | False | 3/3 |

### `data/processed/observed/mbmt_published_bus_allocations.csv`

72 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | mbmt_operator_profile | 72/72 |
| `source_sha256` | str | 296701daaa7ac699030e7049ff91630... | 72/72 |
| `source` | str | undated_municipal_operator_profile | 72/72 |
| `model_ready` | str | False | 72/72 |
| `status` | str | reference_date_and_current_oper... | 72/72 |
| `source_row_sequence` | int | 1 | 72/72 |
| `source_serial_raw` | str | 1 | 72/72 |
| `route_label_raw` | str | 1 | 69/72 |
| `route_name_raw` | str | Bhayandar Station (W) to Chowk | 69/72 |
| `day_type_raw` | str | Monday.to.Friday. | 72/72 |
| `buses_count` | int | 5 | 72/72 |
| `is_subtotal` | str | False | 72/72 |

### `data/processed/observed/mbmt_published_fleet.csv`

3 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | mbmt_operator_profile | 3/3 |
| `source_sha256` | str | 296701daaa7ac699030e7049ff91630... | 3/3 |
| `source` | str | undated_municipal_operator_profile | 3/3 |
| `model_ready` | str | False | 3/3 |
| `status` | str | reference_date_and_current_oper... | 3/3 |
| `vehicle_description_raw` | str | Tata Midi Buses | 3/3 |
| `capacity_expression_raw` | str | Tata Midi Buses ( Migrant capac... | 3/3 |
| `capacity_component_a_persons` | int | 34 | 3/3 |
| `capacity_component_b_persons` | int | 9 | 3/3 |
| `total_capacity_persons` | int | 43 | 3/3 |
| `component_labels_status` | str | seated_standing_labels_not_expl... | 3/3 |
| `published_buses_count` | int | 10 | 3/3 |

### `data/processed/observed/mbmt_route_details.csv`

2078 rows, 10 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `route_id` | int | 5648 | 401/401 |
| `response_sequence` | int | 1 | 401/401 |
| `source_id` | str | mbmt_route_details_5648 | 401/401 |
| `source_sha256` | str | 38a3ce0becb690ce97e656b502848a8... | 401/401 |
| `source` | str | operator_passenger_query | 401/401 |
| `model_ready` | str | False | 401/401 |
| `station_id_raw` | int | 2 | 401/401 |
| `station_name_raw` | str | Bhayandar Station West | 401/401 |
| `published_cumulative_distance_km` | float | 0 | 401/401 |
| `published_cumulative_time_min` | int | 0 | 401/401 |

### `data/processed/observed/mbmt_route_stops.csv`

2078 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `route_id` | int | 5648 | 401/401 |
| `response_sequence` | int | 1 | 401/401 |
| `source_id` | str | mbmt_route_stops_5648 | 401/401 |
| `source_sha256` | str | c10dabd9414b918cc95fd899415697c... | 401/401 |
| `source` | str | operator_passenger_query | 401/401 |
| `model_ready` | str | False | 401/401 |
| `response_route_id` | int | 5648 | 401/401 |
| `route_name_raw` | str | Bhayandar Station W To Chowk | 401/401 |
| `station_name_raw` | str | Bhayandar Station West | 401/401 |
| `api_lat1_deg` | float | 19.31376000 | 401/401 |
| `api_long1_deg` | float | 72.85121000 | 401/401 |
| `direction_raw` | str | Up | 401/401 |

### `data/processed/observed/mbmt_route_vertices.csv`

60673 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `route_id` | int | 5648 | 401/401 |
| `response_sequence` | int | 1 | 401/401 |
| `source_id` | str | mbmt_route_path_5648 | 401/401 |
| `source_sha256` | str | f1bcb4b0503fabe691af18a2d9501b5... | 401/401 |
| `source` | str | operator_passenger_query | 401/401 |
| `model_ready` | str | False | 401/401 |
| `response_route_id` | int | 5648 | 401/401 |
| `source_serial` | int | 900034 | 401/401 |
| `route_name_raw` | str | BHAYANDAR STATION W To CHIMAJI ... | 401/401 |
| `api_latitude_field_deg` | float | 72.78321599861306 | 401/401 |
| `api_longitude_field_deg` | float | 19.293460058949837 | 401/401 |
| `depot_id` | int | 359 | 401/401 |

### `data/processed/observed/metro3_chart_fares.csv`

729 rows, 9 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `from_station_code` | str | CUP | 401/401 |
| `to_station_code` | str | CUP | 401/401 |
| `chart_fare_inr` | int | 10 | 401/401 |
| `template_mse` | float | 0.10199535969071724 | 401/401 |
| `template_margin` | float | 0.1947667029774873 | 401/401 |
| `source` | str | derived | 401/401 |
| `status` | str | transcribed_evidence_not_valida... | 401/401 |
| `source_id` | str | metro3_fare_chart_20260918 | 401/401 |
| `source_sha256` | str | 31df5bd9bc8cbb188f78c7c01741774... | 401/401 |

### `data/processed/observed/metro3_gates.csv`

137 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `station_code` | str | ACA | 137/137 |
| `source_gate_ordinal` | int | 1 | 137/137 |
| `gate_name` | str | A2 | 137/137 |
| `gate_code` | empty |  | 0/137 |
| `latitude_deg` | float | 18.9963 | 71/137 |
| `longitude_deg` | float | 72.8184 | 71/137 |
| `source_gate_latitude` | float | 18.9963 | 75/137 |
| `source_gate_longitude` | float | 72.8184 | 75/137 |
| `coordinate_status` | str | range_checked_only | 137/137 |
| `source_status` | str | open | 137/137 |
| `divyang_friendly_declared` | str | False | 137/137 |
| `source` | str | observed | 137/137 |
| `source_id` | str | mmrcl_station_aca | 137/137 |
| `source_sha256` | str | 30fa602b8481d4f78fc0451b371ab71... | 137/137 |

### `data/processed/observed/metro3_journey_segments.csv`

26 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `sequence` | int | 1 | 26/26 |
| `from_station_code` | str | ARYJ | 26/26 |
| `to_station_code` | str | SEPZ | 26/26 |
| `distance_m` | int | 1482.000 | 26/26 |
| `ordinary_fare_inr` | int | 10 | 26/26 |
| `source_total_time` | str | 0:00:00 | 26/26 |
| `running_time_s` | empty |  | 0/26 |
| `time_status` | str | unvalidated_operator_value | 26/26 |
| `source` | str | observed | 26/26 |
| `source_id` | str | mmrcl_journey_aryj_sepz_20260918 | 26/26 |
| `source_sha256` | str | 512ec84b60ed9cc67ffaf1d0f1491f7... | 26/26 |

### `data/processed/observed/metro3_neighbours.csv`

48 rows, 7 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `station_code` | str | ACA | 48/48 |
| `neighbour_code` | str | WOR | 48/48 |
| `direction` | str | prev_station | 48/48 |
| `line_name` | str | Line 3 | 48/48 |
| `source` | str | observed | 48/48 |
| `source_id` | str | mmrcl_station_aca | 48/48 |
| `source_sha256` | str | 30fa602b8481d4f78fc0451b371ab71... | 48/48 |

### `data/processed/observed/metro3_stations.csv`

27 rows, 10 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `station_code` | str | ACA | 27/27 |
| `afc_station_code` | str | ACA | 27/27 |
| `station_name` | str | Acharya Atre Chowk | 27/27 |
| `latitude_deg` | float | 18.997126 | 27/27 |
| `longitude_deg` | float | 72.818179 | 27/27 |
| `source_type_label` | str | Underground | 27/27 |
| `interchange_declared` | str | False | 27/27 |
| `source` | str | observed | 27/27 |
| `source_id` | str | mmrcl_station_aca | 27/27 |
| `source_sha256` | str | 30fa602b8481d4f78fc0451b371ab71... | 27/27 |

### `data/processed/observed/metro_fleet_publication_claims.csv`

8 rows, 17 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | published_specification | 8/8 |
| `source_id` | str | alstom_metro3_opening_2024 | 8/8 |
| `source_sha256` | str | 5631f09325dc7e62b53609a414c3138... | 8/8 |
| `source_url` | str | https://www.alstom.com/sites/al... | 8/8 |
| `publication_date` | str | 2024-10-05 | 8/8 |
| `route_scope` | str | Mumbai Metro Line 3 | 8/8 |
| `metric` | str | contracted_trainsets | 8/8 |
| `value` | int | 31 | 8/8 |
| `unit` | str | trainsets | 8/8 |
| `qualifier` | str | contract_scope | 8/8 |
| `source_anchor` | str | PDF page 1, engagement paragraph | 8/8 |
| `seats_count` | empty |  | 0/8 |
| `standing_places_count` | empty |  | 0/8 |
| `standing_density_persons_per_m2` | empty |  | 0/8 |
| `capacity_split_status` | str | not_stated_in_publication | 8/8 |
| `operational_trip_assignment_status` | str | unresolved | 8/8 |
| `model_input_status` | str | evidence_only_not_adopted | 8/8 |

### `data/processed/observed/mmr_ena_villages_2024.csv`

446 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `serial_number` | int | 1 | 401/401 |
| `village_name` | str | Ghivali | 401/401 |
| `taluka_name` | str | Palghar | 401/401 |
| `district_name` | str | Palghar | 401/401 |
| `district_urban_annotation` | str | false | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | mmr_ena_spa_notification_20240709 | 401/401 |
| `source_sha256` | str | ceb9aa9713a214001210571935eff7e... | 401/401 |
| `source_pdf_page` | int | 29 | 401/401 |
| `notification_date` | str | 2024-07-09 | 401/401 |
| `status` | str | planning_list_only_boundary_rec... | 401/401 |

### `data/processed/observed/mrvc_rail_control_claims_2023_24.csv`

8 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_historical_publication... | 8/8 |
| `source_id` | str | mrvc_annual_2023_24 | 8/8 |
| `source_sha256` | str | 67c7ff9e579f5b2575d494754ea71a3... | 8/8 |
| `source_pdf_page` | int | 134 | 8/8 |
| `source_printed_page` | int | 10 | 8/8 |
| `reporting_period` | str | 2023-24 | 8/8 |
| `current_model_parameter_adopted` | str | False | 8/8 |
| `metric` | str | existing_lines | 8/8 |
| `reported_value` | float | 2 | 8/8 |
| `units` | str | lines | 8/8 |
| `geographic_scope` | str | Kalyan-Badlapur existing mixed-... | 8/8 |
| `status_scope` | str | historical_existing_infrastruct... | 8/8 |
| `qualifier` | str | as_reported_not_verified_current | 8/8 |
| `source_anchor` | str | existing two lines between KYN-BUD | 8/8 |

### `data/processed/observed/mts_2017_office_category_stock.csv`

1536 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `office_label` | str | Mumbai (C) | 401/401 |
| `column_1_based` | int | 1 | 401/401 |
| `measure` | str | registered_stock_20170331 | 401/401 |
| `office_level` | str | office | 401/401 |
| `category_code` | str | 1 | 401/401 |
| `printed_category_label` | str | 1 Motor Cycles | 401/401 |
| `vehicles_count` | int | 316386 | 401/401 |
| `aggregate_row` | str | False | 401/401 |
| `source_page` | int | 59 | 401/401 |
| `source` | str | published_transport_statistics_... | 401/401 |
| `source_sha256` | str | a75c07e8a5da3fbef9b368d4c2458ad... | 401/401 |

### `data/processed/observed/mts_state_category_stock_series.csv`

117 rows, 8 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `table` | str | table_15 | 117/117 |
| `category_serial` | str | 1 | 117/117 |
| `category` | str | Two Wheelers | 117/117 |
| `stock_year_31_march` | int | 1971 | 117/117 |
| `vehicles_count` | int | 86749 | 117/117 |
| `source_page` | int | 47 | 117/117 |
| `source` | str | published_transport_statistics_... | 117/117 |
| `source_sha256` | str | a75c07e8a5da3fbef9b368d4c2458ad... | 117/117 |

### `data/processed/observed/mumbai_port_monthly_rakes.csv`

264 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | mumbai_port_rail_1778075791 | 264/264 |
| `source_sha256` | str | 6ff55705ed3e51ad645d07701f142d9... | 264/264 |
| `source_page` | int | 1 | 264/264 |
| `direction` | str | inward | 264/264 |
| `fiscal_year` | str | 2025-26 | 264/264 |
| `month_label` | str | Apr-25 | 264/264 |
| `measure` | str | loaded_rakes | 264/264 |
| `value_count` | int | 3 | 264/264 |
| `source` | str | operator_reported | 264/264 |
| `derived_from` | str | loaded_rakes - (loaded_muriate_... | 1/264 |
| `raw_cell_blank` | str | False | 264/264 |
| `is_subtotal` | str | True | 264/264 |

### `data/processed/observed/navi_metro_reported_controls.csv`

16 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | mahametro_current_annual_2024_25 | 16/16 |
| `source_sha256` | str | aff714b443ee1c83e9e438f345d3c15... | 16/16 |
| `source_page` | int | 30 | 16/16 |
| `operator` | str | Maha Metro for CIDCO | 16/16 |
| `line` | str | Navi Mumbai Metro Line 1 | 16/16 |
| `measure` | str | average_daily_ridership | 16/16 |
| `value_in_stated_unit` | str | 10304 | 16/16 |
| `stated_unit` | str | passenger_journeys_per_day | 16/16 |
| `period_or_effective_date` | str | 2024-04 | 16/16 |
| `precision_note` | str | Published integer daily average... | 16/16 |
| `source` | str | operator_reported | 16/16 |
| `validation_status` | str | historical_source_not_current_c... | 16/16 |

### `data/processed/observed/nfhs_household_vehicle_possession.csv`

18 rows, 13 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `survey` | str | NFHS-4 | 18/18 |
| `reference_period` | str | 2015-16 | 18/18 |
| `state` | str | Maharashtra | 18/18 |
| `residence` | str | urban | 18/18 |
| `item` | str | bicycle | 18/18 |
| `households_possessing_pct` | float | 30.4 | 18/18 |
| `universe` | str | households (de jure population ... | 18/18 |
| `source` | str | observed | 18/18 |
| `source_id` | str | nfhs4_maharashtra_report_2015_16 | 18/18 |
| `source_sha256` | str | 287318f787280797305fac0a58686ef... | 18/18 |
| `source_page` | int | 47 | 18/18 |
| `source_table` | str | Table 5 Household possessions a... | 18/18 |
| `status` | str | state_survey_observation_not_di... | 18/18 |

### `data/processed/observed/nmmt_departures.csv`

9522 rows, 10 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `route_id` | int | 5578 | 401/401 |
| `trip_id` | int | 21151 | 401/401 |
| `route_number` | str | 002 | 401/401 |
| `from_station_id` | int | 3173 | 401/401 |
| `to_station_id` | int | 3156 | 401/401 |
| `published_departure_time` | str | 12:03 PM | 401/401 |
| `departure_clock_s` | int | 43380 | 401/401 |
| `calendar_status` | str | unresolved | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | nmmt_schedule_5578 | 401/401 |

### `data/processed/observed/nmmt_route_stop_snapshots.csv`

18146 rows, 22 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | nmmt_route_live_5578_20260918 | 401/401 |
| `queried_route_id` | int | 5578 | 401/401 |
| `direction` | str | down | 401/401 |
| `response_sequence` | int | 1 | 401/401 |
| `returned_route_id` | int | 5578 | 401/401 |
| `station_id` | int | 3173 | 401/401 |
| `station_name` | str | Thane | 401/401 |
| `route_number` | str | 002 | 401/401 |
| `latitude_deg` | float | 19.18808 | 401/401 |
| `longitude_deg` | float | 72.97973 | 401/401 |
| `coordinate_valid` | str | True | 401/401 |
| `distance_on_station_raw` | float | 0.0 | 401/401 |
| `distance_between_stops_raw` | float | 0.0 | 401/401 |
| `cumulative_distance_km` | float | 0.0 | 401/401 |
| `vehicle_indications_count` | int | 0 | 401/401 |
| `stop_to_published_geometry_m` | float | 31.279738326515908 | 401/401 |
| `projected_along_geometry_m` | float | 25203.62994702987 | 401/401 |
| `geometry_source_sha256` | str | 32cefe7506510b0ddc4db38f321f0b4... | 401/401 |
| `projected_epsg` | int | 32643 | 401/401 |
| `retrieved` | str | 2026-09-18T11:35:18.838749+00:00 | 401/401 |
| `source` | str | operator_passenger_snapshot | 401/401 |
| `source_sha256` | str | fbe37a890d6c2e816d6b0dbb21c2610... | 401/401 |

### `data/processed/observed/nmmt_route_vertices.csv`

518782 rows, 9 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `route_id` | int | 5578 | 401/401 |
| `response_sequence` | int | 1 | 401/401 |
| `route_path_map_id` | int | 1909763 | 401/401 |
| `latitude_deg` | float | 19.187672702743157 | 401/401 |
| `longitude_deg` | float | 72.97941154442466 | 401/401 |
| `coordinate_status` | str | valid_range | 401/401 |
| `source` | str | operator_published_map | 401/401 |
| `source_id` | str | nmmt_route_path_5578 | 401/401 |
| `source_sha256` | str | 32cefe7506510b0ddc4db38f321f0b4... | 401/401 |

### `data/processed/observed/nmmt_stop_times.csv`

367221 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `route_id` | int | 5578 | 401/401 |
| `trip_id` | int | 21151 | 401/401 |
| `stop_sequence` | int | 1 | 401/401 |
| `published_stop_name` | str | Thane | 401/401 |
| `published_stop_time` | str | 12:03 PM | 401/401 |
| `stop_clock_s` | int | 43380 | 401/401 |
| `station_id` | int | 3173 | 401/401 |
| `candidate_station_ids` | int | 3173 | 401/401 |
| `station_match_status` | str | unique_exact_name | 401/401 |
| `calendar_status` | str | unresolved | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | nmmt_trip_5578_21151 | 401/401 |

### `data/processed/observed/nmmt_vehicle_indications.csv`

1832 rows, 26 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | nmmt_route_live_5615_20260918 | 401/401 |
| `queried_route_id` | int | 5615 | 401/401 |
| `returned_route_id` | int | 5615 | 401/401 |
| `direction` | str | down | 401/401 |
| `station_id` | int | 2908 | 401/401 |
| `response_stop_sequence` | int | 1 | 401/401 |
| `vehicle_id` | int | 648 | 401/401 |
| `tracking_trip_id` | int | 567783680 | 401/401 |
| `service_type_id` | int | 2 | 401/401 |
| `reported_latitude_deg` | float | 19.123484 | 401/401 |
| `reported_longitude_deg` | float | 73.001198 | 401/401 |
| `refresh_time_raw` | str | 18-09-2026 17:04:36 | 401/401 |
| `refresh_flag_raw` | int | 0 | 401/401 |
| `scheduled_arrival_raw` | str | 16:44 | 401/401 |
| `scheduled_departure_raw` | str | 16:44 | 401/401 |
| `actual_arrival_raw` | str | 17:00 | 147/401 |
| `actual_departure_raw` | str | 17:00 | 144/401 |
| `scheduled_trip_start_raw` | str | 16:44 | 401/401 |
| `scheduled_trip_end_raw` | str | 16:44 | 401/401 |
| `eta_raw` | str | 17:06 | 195/401 |
| `stop_covered_status_raw` | int | 1 | 401/401 |
| `current_location_id` | int | 0 | 401/401 |
| `next_location_id` | int | 0 | 401/401 |
| `retrieved_utc` | str | 2026-09-18T11:35:22.139796+00:00 | 401/401 |
| `source` | str | operator_reported_vehicle_indic... | 401/401 |
| `source_sha256` | str | 78a39ab85f9b60f6a28ed53a8380676... | 401/401 |

### `data/processed/observed/nmmt_vehicle_locations.csv`

36 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | nmmt_vehicle_277_20260918 | 36/36 |
| `vehicle_id` | int | 277 | 36/36 |
| `reported_latitude_deg` | float | 18.991165000000002 | 36/36 |
| `reported_longitude_deg` | float | 73.12347833333334 | 36/36 |
| `last_refresh_raw` | str | 18-09-2026 17:04:48 | 36/36 |
| `refresh_flag_raw` | int | 1 | 36/36 |
| `speed_raw` | float | 3.7 | 36/36 |
| `fuel_type_raw` | str | Diesel | 36/36 |
| `source` | str | operator_reported_vehicle_location | 36/36 |
| `retrieved_utc` | str | 2026-09-18T11:53:40.765458+00:00 | 36/36 |
| `source_sha256` | str | c9058bc02c95a21ccdf249949b3b605... | 36/36 |

### `data/processed/observed/nmmt_vehicle_stop_details.csv`

1560 rows, 24 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | nmmt_vehicle_293_20260918 | 401/401 |
| `queried_vehicle_id` | int | 293 | 401/401 |
| `returned_vehicle_id` | int | 293 | 401/401 |
| `tracking_trip_id` | int | 567784860 | 401/401 |
| `route_id` | int | 6975 | 401/401 |
| `station_id` | int | 3461 | 401/401 |
| `response_sequence` | int | 1 | 401/401 |
| `published_sequence` | int | 181712273 | 401/401 |
| `trip_status_raw` | str | Running | 401/401 |
| `stop_status_raw` | str | covered | 401/401 |
| `scheduled_arrival_raw` | str | 16:42:00 | 401/401 |
| `scheduled_departure_raw` | str | 16:42:00 | 401/401 |
| `scheduled_arrival_datetime_raw` | str | 2026-09-18T16:42:00 | 401/401 |
| `actual_arrival_field_raw` | str | 16:55:50 | 401/401 |
| `actual_departure_field_raw` | str | 16:56:00 | 182/401 |
| `covered_with_both_actual_fields` | str | True | 401/401 |
| `actual_arrival_equals_schedule` | str | False | 401/401 |
| `reported_trip_start_raw` | str | 16:42 | 401/401 |
| `reported_trip_end_raw` | str | 17:05 | 401/401 |
| `last_updated_raw` | str | 18-09-2026 17:07:10 | 401/401 |
| `refresh_flag_raw` | int | 1 | 401/401 |
| `source` | str | operator_reported_trip_stop | 401/401 |
| `retrieved_utc` | str | 2026-09-18T11:37:53.521451+00:00 | 401/401 |
| `source_sha256` | str | ba0fc4bc49a545324f065cfeefd55e1... | 401/401 |

### `data/processed/observed/ogd_metro_daily_ridership.csv`

984 rows, 13 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `line` | str | Metro Lines 2A and 7 | 401/401 |
| `date` | str | 2024-01-01 | 401/401 |
| `weekday` | str | True | 401/401 |
| `paper_qr` | int | 105702 | 401/401 |
| `mobile_application` | int | 3294 | 401/401 |
| `whatsapp` | int | 0 | 401/401 |
| `ncmc_and_other_trip` | int | 32577 | 401/401 |
| `total_ridership` | int | 141573 | 401/401 |
| `channel_sum_equals_total` | str | True | 401/401 |
| `source` | str | observed | 401/401 |
| `source_id` | str | ogd_metro_2a_7_ridership_daily_... | 401/401 |
| `source_sha256` | str | 46e3b6fd316a2ba8e33e077bb9c5855... | 401/401 |
| `printed_line` | str | 2A & 7 | 401/401 |

### `data/processed/observed/osm_transport_points.csv`

12009 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `osm_node_id` | int | 30518270 | 401/401 |
| `name` | str | Vasai Road | 53/401 |
| `longitude_deg` | float | 72.85292600000001 | 401/401 |
| `latitude_deg` | float | 19.306538 | 401/401 |
| `x_m` | float | 274396.1748674371 | 401/401 |
| `y_m` | float | 2136143.7974510132 | 401/401 |
| `projected_epsg` | int | 32643 | 401/401 |
| `selected_tags_json` | str | {"railway": "switch"} | 401/401 |
| `all_driver_tags_json` | str | {"railway": "switch"} | 401/401 |
| `source` | str | mapped_osm_feature | 401/401 |
| `status` | str | unverified_operation_and_statio... | 401/401 |

### `data/processed/observed/osm_transport_relations.csv`

1811 rows, 17 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | mapped_osm_relation | 401/401 |
| `osm_relation_id` | int | 278091 | 401/401 |
| `source_native_sha256` | str | 88f47570e3d22cbbf1b02a36ff24dca... | 401/401 |
| `source_pbf_sha256` | str | c335a72cadfebc3ffde5cfff20fc971... | 401/401 |
| `relation_type` | str | route | 401/401 |
| `public_transport_tag` | str | stop_area | 114/401 |
| `route_tag` | str | road | 257/401 |
| `route_master_tag` | str | train | 18/401 |
| `name` | str | Old National Highway 4 | 307/401 |
| `ref` | str | KR | 234/401 |
| `network` | str | IN:NH | 274/401 |
| `operator` | str | Ministry of Railways | 160/401 |
| `selection_basis` | str | direct_research_geometry_member | 401/401 |
| `member_count` | int | 3378 | 401/401 |
| `ordered_members_json` | str | [{"type":"way","ref":"119972534... | 401/401 |
| `all_tags_json` | str | {"description": "NH48 route pri... | 401/401 |
| `status` | str | membership_evidence_not_operati... | 401/401 |

### `data/processed/observed/published_mode_splits.csv`

33 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | cts_2021_mirror | 33/33 |
| `source_sha256` | str | 025fa4604a024210f3e523665c8ab84... | 33/33 |
| `source_pdf_page` | int | 109 | 33/33 |
| `table` | str | Table 6-8 Daily Mode Split, Mum... | 33/33 |
| `area` | str | Mumbai Metropolitan Region | 33/33 |
| `survey_year` | int | 2017 | 33/33 |
| `mode_raw` | str | Metro & Mono | 33/33 |
| `trips_per_day` | int | 410000 | 32/33 |
| `share_pct` | float | 2.2 | 33/33 |
| `share_basis` | str | motorised main-mode trips per day | 33/33 |
| `status` | str | observed_published_table | 33/33 |

### `data/processed/observed/rail_capacity_claims_20260325.csv`

6 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_official_publication_c... | 6/6 |
| `source_id` | str | pib_mumbai_rail_capacity_projec... | 6/6 |
| `source_sha256` | str | 01bf7104e08c403c1fd1813fcb35b5a... | 6/6 |
| `publication_date` | str | 2026-03-25 | 6/6 |
| `current_model_supply_adopted` | str | False | 6/6 |
| `metric` | str | originating_mail_express | 6/6 |
| `reported_value` | int | 120 | 6/6 |
| `units` | str | train_services_per_day | 6/6 |
| `qualifier` | str | around | 6/6 |
| `status_scope` | str | dated_approximate_operational_a... | 6/6 |
| `source_anchor` | str | Opening Mumbai paragraph | 6/6 |

### `data/processed/observed/rail_corridor_project_status_20260325.csv`

13 rows, 13 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_official_publication_c... | 13/13 |
| `source_id` | str | pib_mumbai_rail_capacity_projec... | 13/13 |
| `source_sha256` | str | 01bf7104e08c403c1fd1813fcb35b5a... | 13/13 |
| `publication_date` | str | 2026-03-25 | 13/13 |
| `current_model_supply_adopted` | str | False | 13/13 |
| `source_table` | str | New projects for increasing cap... | 13/13 |
| `source_row` | int | 1 | 13/13 |
| `project_as_printed` | str | CSMT-Kurla 5th & 6th Line (MUTP... | 13/13 |
| `stated_project_length_km` | float | 17.5 | 12/13 |
| `stated_cost_INR_crore` | int | 891 | 13/13 |
| `status_scope` | str | sanctioned_project_not_proof_of... | 13/13 |
| `commissioned_date` | empty |  | 0/13 |
| `operational_capacity_status` | str | not_established_by_this_table | 13/13 |

### `data/processed/observed/rail_terminal_project_status_20260325.csv`

12 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_official_publication_c... | 12/12 |
| `source_id` | str | pib_mumbai_rail_capacity_projec... | 12/12 |
| `source_sha256` | str | 01bf7104e08c403c1fd1813fcb35b5a... | 12/12 |
| `publication_date` | str | 2026-03-25 | 12/12 |
| `current_model_supply_adopted` | str | False | 12/12 |
| `source_table` | str | Capacity Augmentation works for... | 12/12 |
| `source_row` | int | 1 | 12/12 |
| `location_as_printed` | str | Bandra Terminus | 12/12 |
| `details_as_printed` | str | 3 Pit Lines have been completed | 12/12 |
| `status_scope` | str | completed_as_stated | 12/12 |
| `commissioned_date` | empty |  | 0/12 |
| `operational_capacity_status` | str | not_established_by_this_table | 12/12 |

### `data/processed/observed/rto_2025_summary.csv`

65 rows, 6 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `office_label` | str | Mumbai (C) | 65/65 |
| `registered_stock_20250331_count` | int | 1462861 | 65/65 |
| `new_registrations_2024_25_count` | int | 82774 | 65/65 |
| `source_page` | int | 1 | 65/65 |
| `source` | str | published_registration_statistics | 65/65 |
| `source_sha256` | str | 66426e585d9e275def066a350067f26... | 65/65 |

### `data/processed/observed/rto_2025_vehicle_categories.csv`

3120 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `office_label` | str | Mumbai (C) | 401/401 |
| `column_1_based` | int | 1 | 401/401 |
| `measure` | str | registered_stock_20250331 | 401/401 |
| `office_level` | str | office | 401/401 |
| `category_code` | str | 1 | 401/401 |
| `printed_category_label` | str | 1 Motor Cycles | 401/401 |
| `vehicles_count` | int | 647628 | 401/401 |
| `aggregate_row` | str | False | 401/401 |
| `source_page` | int | 3 | 401/401 |
| `source` | str | published_provisional_registrat... | 401/401 |
| `source_sha256` | str | 66426e585d9e275def066a350067f26... | 401/401 |
| `validation_status` | str | arithmetic_checked_not_spatiall... | 401/401 |

### `data/processed/observed/scheduled_area_name_candidates.csv`

189 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | derived | 189/189 |
| `source_id` | str | maharashtra_scheduled_areas_ord... | 189/189 |
| `source_sha256` | str | f9688f5830373c805bdb4b86f4e9f46... | 189/189 |
| `source_pdf_page` | int | 8 | 189/189 |
| `notification_date` | str | 1985-12-02 | 189/189 |
| `district_name_as_printed` | str | Thane | 189/189 |
| `taluka_name` | str | Palghar | 189/189 |
| `serial_number` | int | 1 | 189/189 |
| `village_name_as_transcribed` | str | Tarapur | 189/189 |
| `transcription_status` | str | english_scan_visually_transcribed | 189/189 |
| `census_name_candidate_count` | int | 1 | 189/189 |
| `census_name_candidates_json` | str | [{"level": "TOWN", "name": "Tar... | 189/189 |
| `ena_name_candidate_count` | int | 0 | 189/189 |
| `ena_name_candidate_serials` | int | 4 | 98/189 |
| `ena_candidate_names` | str | Kudan | 98/189 |
| `boundary_status` | str | unresolved_no_inclusion_or_excl... | 189/189 |

### `data/processed/observed/srtu_historical_controls.csv`

255 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `operator_name` | str | Maharashtra SRTC | 255/255 |
| `source_row_serial` | int | 11 | 255/255 |
| `financial_year` | str | 2021-22 | 255/255 |
| `metric` | str | average_fleet_held | 255/255 |
| `value_as_printed` | str | 17,120 | 255/255 |
| `numeric_value` | float | 17120 | 234/255 |
| `unit` | str | buses_count | 255/255 |
| `reported_status` | str | reported | 255/255 |
| `source` | str | operator_reported_in_official_c... | 255/255 |
| `source_id` | str | morth_srtu_review_2019_2022 | 255/255 |
| `source_sha256` | str | 9a9d5693d36372181d5db95c9f776e2... | 255/255 |
| `source_page_1_based` | int | 110 | 255/255 |
| `model_ready` | str | False | 255/255 |
| `geography_scope` | str | statewide_not_mmr | 255/255 |

### `data/processed/observed/state_age_population_projection_shares.csv`

108 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | modelled | 108/108 |
| `source_id` | str | nhm_population_projection_2019 | 108/108 |
| `source_sha256` | str | 9a9031c9c75d609e03ab94ce0ac6115... | 108/108 |
| `source_pdf_page` | int | 235 | 108/108 |
| `source_table` | int | 19 | 108/108 |
| `publisher_edition` | str | November 2019 | 108/108 |
| `area_name` | str | Maharashtra | 108/108 |
| `geography_level` | str | state | 108/108 |
| `status` | str | published_projection_or_smoothe... | 108/108 |
| `reference_date` | str | 2011-03-01 | 108/108 |
| `age_label` | str | 0-4 | 108/108 |
| `age_partition` | str | five_year_or_open | 108/108 |
| `persons_percent` | float | 8.5 | 108/108 |
| `male_percent` | float | 8.6 | 108/108 |
| `female_percent` | float | 8.4 | 108/108 |

### `data/processed/observed/state_age_population_projections.csv`

234 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | modelled | 234/234 |
| `source_id` | str | nhm_population_projection_2019 | 234/234 |
| `source_sha256` | str | 9a9031c9c75d609e03ab94ce0ac6115... | 234/234 |
| `source_pdf_page` | int | 234 | 234/234 |
| `source_table` | int | 18 | 234/234 |
| `publisher_edition` | str | November 2019 | 234/234 |
| `area_name` | str | Maharashtra | 234/234 |
| `geography_level` | str | state | 234/234 |
| `status` | str | published_projection_or_smoothe... | 234/234 |
| `reference_date` | str | 2011-03-01 | 234/234 |
| `age_label` | str | 0-1 | 234/234 |
| `age_partition` | str | supplementary_overlapping | 234/234 |
| `persons_thousands_count` | int | 1921 | 234/234 |
| `male_thousands_count` | int | 1008 | 234/234 |
| `female_thousands_count` | int | 913 | 234/234 |
| `unit_basis` | str | printed_table_18_heading | 234/234 |

### `data/processed/observed/state_education_controls.csv`

173 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `dataset` | str | udise | 173/173 |
| `indicator_code` | int | 1 | 173/173 |
| `indicator` | str | Total number of School | 173/173 |
| `observation_year` | str | 2024-25 | 173/173 |
| `region` | str | Maharashtra | 173/173 |
| `dimensions_json` | str | {} | 173/173 |
| `reported_count` | int | 108250 | 173/173 |
| `source` | str | published_statistic | 173/173 |
| `source_id` | str | mospi_udise_2024-25_maharashtra... | 173/173 |
| `source_sha256` | str | da41f0f4046c09ea2f9e57716b5836b... | 173/173 |
| `status` | str | state_aggregate_not_local_trip_... | 173/173 |

### `data/processed/observed/state_population_projections.csv`

156 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | modelled | 156/156 |
| `source_id` | str | nhm_population_projection_2019 | 156/156 |
| `source_sha256` | str | 9a9031c9c75d609e03ab94ce0ac6115... | 156/156 |
| `source_pdf_page` | int | 52 | 156/156 |
| `source_table` | int | 8 | 156/156 |
| `publisher_edition` | str | November 2019 | 156/156 |
| `area_name` | str | Maharashtra | 156/156 |
| `geography_level` | str | state | 156/156 |
| `status` | str | published_projection_or_smoothe... | 156/156 |
| `reference_date` | str | 2011-03-01 | 156/156 |
| `residence` | str | Total | 156/156 |
| `persons_thousands_count` | int | 112374 | 156/156 |
| `male_thousands_count` | int | 58243 | 156/156 |
| `female_thousands_count` | int | 54131 | 156/156 |

### `data/processed/observed/state_time_use_controls.csv`

405 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `region` | str | Maharashtra | 401/401 |
| `observation_year` | int | 2024 | 401/401 |
| `minimum_age_years` | int | 6 | 401/401 |
| `activity` | str | Employment and related activities | 401/401 |
| `residence` | str | rural | 401/401 |
| `sex` | str | male | 401/401 |
| `activity_scope` | str | major_activity | 401/401 |
| `denominator` | str | participation | 401/401 |
| `value` | float | 66.3 | 401/401 |
| `unit` | str | percent | 401/401 |
| `source` | str | published_survey_estimate | 401/401 |
| `source_id` | str | tus_2024_report | 401/401 |
| `source_sha256` | str | a4380137658c886985c5312c199dc71... | 401/401 |
| `statement` | float | 3.1 | 401/401 |
| `pdf_page` | int | 101 | 401/401 |
| `status` | str | state_benchmark_not_local_diary | 401/401 |

### `data/processed/observed/suburban_first_ac_capacity_2017.csv`

4 rows, 15 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | published_design_capacity | 4/4 |
| `source_id` | str | pib_first_ac_emu_2017 | 4/4 |
| `source_sha256` | str | 3115541f37f3cfac581aeac821a6264... | 4/4 |
| `publication_date` | str | 2017-12-24 | 4/4 |
| `fleet_scope` | str | first_BHEL_12_car_AC_rake_intro... | 4/4 |
| `capacity_scope` | str | Driving Motor Coach | 4/4 |
| `seats_persons` | int | 65 | 4/4 |
| `standing_places_persons` | int | 258 | 4/4 |
| `total_capacity_persons` | int | 323 | 4/4 |
| `units` | str | persons_per_coach | 4/4 |
| `formation_cars` | int | 12 | 4/4 |
| `source_anchor` | str | Passenger Carrying Capacity Coa... | 4/4 |
| `standing_density_persons_per_m2` | empty |  | 0/4 |
| `standing_density_status` | str | not_stated_in_this_publication | 4/4 |
| `operational_assignment_status` | str | historical_design_not_assigned_... | 4/4 |

### `data/processed/observed/suburban_service_counts_202604.csv`

8 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | pib_suburban_services_20260402 | 8/8 |
| `source_sha256` | str | 135094e6b45aff79b9d2433327c799f... | 8/8 |
| `publication_date` | str | 2026-04-02 | 8/8 |
| `reference_day` | str | not_explicitly_dated_beyond_pre... | 8/8 |
| `current_trip_assignment_status` | str | unresolved | 8/8 |
| `source` | str | published_operational_count | 8/8 |
| `operator` | str | WR | 8/8 |
| `category` | str | All EMU local services | 8/8 |
| `daily_services_count` | int | 1414 | 8/8 |
| `counting_unit` | str | train_service_not_physical_rake... | 8/8 |
| `overlap` | str | AC is a subset of All; WR+CR ov... | 8/8 |
| `source_anchor` | str | Opening paragraph; combined AC ... | 8/8 |

### `data/processed/observed/suburban_stock_claims_202604.csv`

5 rows, 13 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | pib_suburban_services_20260402 | 5/5 |
| `source_sha256` | str | 135094e6b45aff79b9d2433327c799f... | 5/5 |
| `publication_date` | str | 2026-04-02 | 5/5 |
| `reference_day` | str | not_explicitly_dated_beyond_pre... | 5/5 |
| `current_trip_assignment_status` | str | unresolved | 5/5 |
| `source` | str | published_stock_receipt | 5/5 |
| `operator` | str | CR | 5/5 |
| `category` | str | AC EMU | 5/5 |
| `rakes_count` | int | 2 | 5/5 |
| `formation_cars` | int | 12 | 5/5 |
| `reference_period` | str | FY2025-26 | 5/5 |
| `status` | str | received_not_total_active_fleet | 5/5 |
| `source_anchor` | str | Additional rakes item 1 | 5/5 |

### `data/processed/observed/tbtt_2018_reported_aggregates.csv`

11 rows, 16 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | mmrda_thane_borivali_tunnel_dpr | 11/11 |
| `source_sha256` | str | 0eacba038c43131f4926e2e218755e6... | 11/11 |
| `source_pdf_page` | int | 48 | 11/11 |
| `survey_year` | int | 2018 | 11/11 |
| `count_survey_days` | int | 7 | 11/11 |
| `exact_survey_dates` | str | not_stated_in_count_section | 11/11 |
| `units_as_described` | str | average_daily_traffic_counts | 11/11 |
| `class_universe` | str | five_published_groups_not_prove... | 11/11 |
| `target_status` | str | historical_evidence_not_current... | 11/11 |
| `source` | str | derived_by_report | 11/11 |
| `source_table` | str | 2 Average row | 11/11 |
| `aggregate_kind` | str | equal_mean_of_four_different_sites | 11/11 |
| `class_as_printed` | str | Cars | 11/11 |
| `reported_daily_count` | int | 56915 | 11/11 |
| `reference_label` | str | 2018 survey | 11/11 |
| `caveat` | str | not_a_link_count_or_unique_regi... | 11/11 |

### `data/processed/observed/tbtt_2018_site_counts.csv`

20 rows, 17 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | mmrda_thane_borivali_tunnel_dpr | 20/20 |
| `source_sha256` | str | 0eacba038c43131f4926e2e218755e6... | 20/20 |
| `source_pdf_page` | int | 48 | 20/20 |
| `survey_year` | int | 2018 | 20/20 |
| `count_survey_days` | int | 7 | 20/20 |
| `exact_survey_dates` | str | not_stated_in_count_section | 20/20 |
| `units_as_described` | str | average_daily_traffic_counts | 20/20 |
| `class_universe` | str | five_published_groups_not_prove... | 20/20 |
| `target_status` | str | historical_evidence_not_current... | 20/20 |
| `source` | str | observed | 20/20 |
| `source_table` | int | 2 | 20/20 |
| `site_id` | int | 1 | 20/20 |
| `location_as_listed` | str | Magathane Midblock (WEH) | 20/20 |
| `location_detail` | str | CVC1 on Dattapada Road accordin... | 20/20 |
| `class_as_printed` | str | Cars | 20/20 |
| `reported_daily_count` | int | 27887 | 20/20 |
| `direction_scope` | str | not_disaggregated_in_table | 20/20 |

### `data/processed/observed/tbtt_travel_times.csv`

6 rows, 22 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed | 6/6 |
| `source_id` | str | mmrda_thane_borivali_tunnel_dpr | 6/6 |
| `source_sha256` | str | 0eacba038c43131f4926e2e218755e6... | 6/6 |
| `source_pdf_page` | int | 54 | 6/6 |
| `source_row` | int | 1 | 6/6 |
| `report_edition` | str | October 2022 | 6/6 |
| `survey_date` | str | not_stated_in_speed_delay_section | 6/6 |
| `route` | str | Magathane - Tikujiniwadi via Gh... | 6/6 |
| `route_scope` | str | complete_circuit_not_single_dir... | 6/6 |
| `route_geometry` | str | not_georeferenced | 6/6 |
| `survey_method` | str | moving_observer | 6/6 |
| `survey_vehicle_class` | str | not_stated | 6/6 |
| `repetitions` | str | not_stated | 6/6 |
| `period_start_local` | str | 08:00 | 6/6 |
| `period_end_local` | str | 11:30 | 6/6 |
| `distance_km` | float | 55.9 | 6/6 |
| `distance_source` | str | merged_cell_PDF54_continued_PDF55 | 6/6 |
| `journey_time_minutes` | float | 198.8 | 6/6 |
| `delay_minutes` | float | 78.03 | 6/6 |
| `reported_journey_speed_kmh` | float | 16.87 | 6/6 |
| `reported_running_speed_kmh` | float | 27.77 | 6/6 |
| `target_status` | str | historical_evidence_not_current... | 6/6 |

### `data/processed/observed/tiss_rail_access_modes_2016.csv`

7 rows, 21 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_historical_survey_publ... | 7/7 |
| `source_id` | str | mrvc_gender_tiss_study | 7/7 |
| `source_sha256` | str | f3b77e0729ee49dcccdf0edf93834a0... | 7/7 |
| `publication_year` | int | 2016 | 7/7 |
| `population_scope` | str | sampled_women_suburban_rail_use... | 7/7 |
| `fieldwork_date_status` | str | full_survey_dates_not_establish... | 7/7 |
| `current_model_parameter_adopted` | str | False | 7/7 |
| `source_pdf_page` | int | 27 | 7/7 |
| `source_printed_page` | int | 23 | 7/7 |
| `source_table` | int | 9 | 7/7 |
| `journey_scope` | str | first_leg_from_home_to_rail_sta... | 7/7 |
| `mode_as_printed` | str | Walk | 7/7 |
| `count_as_printed` | str | 494.0 | 7/7 |
| `reported_respondents_persons` | int | 494 | 6/7 |
| `share_as_printed` | str | 49.7 | 7/7 |
| `reported_share_percent` | float | 49.7 | 6/7 |
| `derived_table_denominator_respondents_persons` | int | 994 | 7/7 |
| `source_value_status` | str | observed_table_cell | 7/7 |
| `recomputed_share_percent` | float | 49.69818913480885311871227364 | 6/7 |
| `reported_minus_recomputed_percentage_points` | float | 0.00181086519114688128772636 | 6/7 |
| `consistent_with_printed_rounding` | str | True | 7/7 |

### `data/processed/observed/tiss_rail_survey_strata_2016.csv`

12 rows, 19 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_historical_survey_publ... | 12/12 |
| `source_id` | str | mrvc_gender_tiss_study | 12/12 |
| `source_sha256` | str | f3b77e0729ee49dcccdf0edf93834a0... | 12/12 |
| `publication_year` | int | 2016 | 12/12 |
| `population_scope` | str | sampled_women_suburban_rail_use... | 12/12 |
| `fieldwork_date_status` | str | full_survey_dates_not_establish... | 12/12 |
| `current_model_parameter_adopted` | str | False | 12/12 |
| `source_pdf_page` | int | 19 | 12/12 |
| `source_printed_page` | int | 15 | 12/12 |
| `source_table` | int | 1 | 12/12 |
| `railway_line_as_printed` | str | Western Line | 12/12 |
| `travel_class_as_printed` | str | All classes | 12/12 |
| `reported_respondents_persons` | int | 463 | 12/12 |
| `reported_share_percent` | float | 46.3 | 12/12 |
| `denominator_respondents_persons` | int | 1000 | 12/12 |
| `denominator_scope` | str | all_sampled_respondents | 12/12 |
| `recomputed_share_percent` | float | 46.3 | 12/12 |
| `reported_minus_recomputed_percentage_points` | float | 0.0 | 12/12 |
| `consistent_with_printed_rounding` | str | True | 12/12 |

### `data/processed/observed/traffic_notice_index.csv`

1870 rows, 13 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | mtp_notice_823392 | 401/401 |
| `notice_id` | str | Notification No 202/DCP/Central... | 401/401 |
| `listed_date` | str | 16/09/2026 | 401/401 |
| `listed_valid_until` | str | Till Next Order | 401/401 |
| `subject` | str | Traffic arrangement | 401/401 |
| `notice_text` | str | Traffic arrangement | 401/401 |
| `attachment_number` | int | 1 | 401/401 |
| `attachment_count` | int | 1 | 401/401 |
| `attachment_url` | str | https://mtperp.mahatrafficechal... | 401/401 |
| `index_source_id` | str | mtp_notifications_20260101_2026... | 401/401 |
| `index_source_sha256` | str | 6de6022c14fc939a6ae0396367758be... | 401/401 |
| `source` | str | official_notice_listing | 401/401 |
| `status` | str | effective_scope_and_supersessio... | 401/401 |

### `data/processed/observed/water_annual_passengers.csv`

111 rows, 14 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `publication_route_id` | int | 1 | 111/111 |
| `port_group` | str | Bandra | 111/111 |
| `route_name` | str | Versova to Madh | 111/111 |
| `financial_year` | str | 2022-23 | 111/111 |
| `reported_passengers_count` | int | 8099632 | 97/111 |
| `reported_count_raw` | str | 80,99,632 | 111/111 |
| `parse_status` | str | numeric | 111/111 |
| `source` | str | reported_observation | 111/111 |
| `source_id` | str | mmb_performance | 111/111 |
| `source_url` | str | https://maharashtramaritimeboar... | 111/111 |
| `source_sha256` | str | 1182f554877f9af09f70e2bc43cdbfd... | 111/111 |
| `count_definition` | str | Published passenger total; jour... | 111/111 |
| `geography_status` | str | Statewide source; MMR membershi... | 111/111 |
| `calibration_eligible` | str | false | 111/111 |

### `data/processed/observed/water_service_directory.csv`

37 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `directory_route_id` | int | 1 | 37/37 |
| `port_group` | str | Bandra | 37/37 |
| `route_name` | str | Versova to Madh | 37/37 |
| `first_departure_raw` | str | 05.30 AM | 33/37 |
| `last_departure_raw` | str | 12.00 AM | 33/37 |
| `fare_raw` | str | Rs 10/-, Rs 5/- | 37/37 |
| `passenger_capacity_raw` | str | 37 (fair season) | 32/37 |
| `source` | str | published_service_directory | 37/37 |
| `source_id` | str | mmb_routes | 37/37 |
| `source_url` | str | https://maharashtramaritimeboar... | 37/37 |
| `source_sha256` | str | 1e7db7900997fb74e1b435c7adde0c7... | 37/37 |
| `validation_status` | str | Units, season, vessel/fleet bas... | 37/37 |

### `data/processed/observed/wr_printed_timetable_cells.csv`

25987 rows, 12 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source_id` | str | wr_public_timetable_attachment_1 | 401/401 |
| `source_sha256` | str | 3cfcb598a5b83b1cffd960db4e8b79d... | 401/401 |
| `source_page` | int | 1 | 401/401 |
| `train_number` | int | 90001 | 401/401 |
| `aligned_station_row_label` | str | BANDRA | 401/401 |
| `station_row_order` | int | 12 | 401/401 |
| `printed_local_hhmm` | str | 04:05 | 401/401 |
| `source_x_pdf_pt` | float | 197.508237 | 401/401 |
| `source_y_pdf_pt` | float | 332.281073 | 401/401 |
| `source` | str | observed | 401/401 |
| `stopping_status` | str | unresolved | 401/401 |
| `validation_status` | str | printed_cell_only_calendar_and_... | 401/401 |

### `data/processed/observed/wr_station_abbreviations.csv`

3 rows, 8 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_railway_publication | 3/3 |
| `source_id` | str | wr_bct_disaster_plan_part1_2025 | 3/3 |
| `source_sha256` | str | 0bd5fd0497f5caf4caee1ec2247fcef... | 3/3 |
| `source_page` | int | 15 | 3/3 |
| `duplicate_source_page` | int | 158 | 3/3 |
| `printed_abbreviation` | str | Jn. | 3/3 |
| `printed_expansion` | str | Junction | 3/3 |
| `evidence_scope` | str | repeated_page_is_not_independen... | 3/3 |

### `data/processed/observed/wr_station_code_reference.csv`

5 rows, 9 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `source` | str | observed_railway_publication | 5/5 |
| `source_id` | str | wr_disaster_plan_part2_2025 | 5/5 |
| `source_sha256` | str | 2dff4567b9c33ca127d1a4b4c2e3822... | 5/5 |
| `source_page` | int | 39 | 5/5 |
| `printed_station_name` | str | MAHIM | 5/5 |
| `printed_station_code` | str | MM | 5/5 |
| `source_name_bbox_pdf_pt` | str | [110.06,127.7816,149.24912,138.... | 5/5 |
| `source_code_bbox_pdf_pt` | str | [202.25,127.7816,223.19912,138.... | 5/5 |
| `evidence_scope` | str | 2025_reference_identity_not_cur... | 5/5 |

## Validation

### `data/processed/validation/mode_targets_by_mode.csv`

13 rows, 9 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `mode` | str | car | 13/13 |
| `target_pct` | float | 2.9132 | 12/13 |
| `denominator` | str | resident person trips | 13/13 |
| `status` | str | derived | 13/13 |
| `sweep_low` | float | 2.7483 | 11/13 |
| `sweep_high` | float | 3.0781 | 11/13 |
| `basis` | str | CTS Updation Table 6-8 (Mumbai ... | 13/13 |
| `target_mean_km` | empty |  | 0/13 |
| `mean_km_basis` | empty |  | 0/13 |

## B1/B2 demand

### `demand/baseline/activities.csv`

1052 rows, 11 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `person_id` | str | baseline_0 | 401/401 |
| `tour_index` | int | 0 | 401/401 |
| `purpose` | str | education | 401/401 |
| `location_id` | str | osm_way_202555853 | 401/401 |
| `destination_geography_id` | str | 27:518:99999:802794:1352:000000 | 336/401 |
| `x_m` | float | 271632.3716605586 | 401/401 |
| `y_m` | float | 2118798.860890519 | 401/401 |
| `duration_s` | int | 21600 | 401/401 |
| `initial_mode` | str | walk | 401/401 |
| `source` | str | synthetic_provisional_activity | 401/401 |
| `destination_source` | str | OSM_area_representative_point_n... | 401/401 |

### `demand/baseline/freight_movements.csv`

282 rows, 8 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `person_id` | str | background_truck_0 | 282/282 |
| `mode` | str | truck | 282/282 |
| `departure_s` | int | 27063 | 282/282 |
| `origin_link_id` | int | 164124 | 282/282 |
| `destination_link_id` | int | 99494 | 282/282 |
| `gate_axis` | str | north | 282/282 |
| `source` | str | modelled_provisional_background... | 282/282 |
| `od_status` | str | port_locality_and_connected_res... | 282/282 |

### `demand/baseline/persons.csv`

1000 rows, 13 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `person_id` | str | baseline_0 | 401/401 |
| `home_geography_id` | str | 27:518:99999:802794:1460:000000 | 401/401 |
| `destination_geography_id` | str | 27:518:99999:802794:1562:000000 | 401/401 |
| `age_years` | int | 16 | 401/401 |
| `sex` | str | female | 401/401 |
| `employed` | str | False | 401/401 |
| `income_monthly_inr` | float | 41656.80495848191 | 401/401 |
| `permitted_modes` | str | walk,pt | 401/401 |
| `purpose` | str | education | 401/401 |
| `initial_mode` | str | walk | 369/401 |
| `departure_s` | float | 31271.662396987165 | 401/401 |
| `activity_duration_s` | int | 21600 | 401/401 |
| `source` | str | synthetic_from_historical_margi... | 401/401 |

### `demand/population/B1_households.csv`

6068786 rows, 6 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `household_id` | int | 1 | 401/401 |
| `geography_id` | str | 27:517:04163:552183:0000:000000 | 401/401 |
| `size` | int | 3 | 401/401 |
| `two_wheelers` | int | 0 | 401/401 |
| `cars` | int | 0 | 401/401 |
| `bicycles` | int | 0 | 401/401 |

### `demand/population/B1_synthetic_population.csv`

27057132 rows, 20 columns

| column | type | example | non-empty in sample |
|---|---|---|---|
| `person_id` | int | 1 | 401/401 |
| `household_id` | int | 1 | 401/401 |
| `geography_id` | str | 27:517:04163:552183:0000:000000 | 401/401 |
| `tier` | str | core | 401/401 |
| `district_code` | int | 517 | 401/401 |
| `rural_urban` | str | Rural | 401/401 |
| `age` | int | 2 | 401/401 |
| `sex` | str | male | 401/401 |
| `worker_status` | str | non_worker | 401/401 |
| `student` | int | 0 | 401/401 |
| `licence_holder` | int | 0 | 401/401 |
| `household_size` | int | 3 | 401/401 |
| `household_two_wheelers` | int | 0 | 401/401 |
| `household_cars` | int | 0 | 401/401 |
| `household_bicycles` | int | 0 | 401/401 |
| `car_available` | int | 0 | 401/401 |
| `two_wheeler_available` | int | 0 | 401/401 |
| `bike_available` | int | 0 | 401/401 |
| `income_monthly_inr` | float | 0.0 | 401/401 |
| `weight` | int | 1.0 | 401/401 |
