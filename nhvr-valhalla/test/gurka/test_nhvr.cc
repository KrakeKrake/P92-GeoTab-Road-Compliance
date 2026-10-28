#include "gurka.h"
#include "test.h"
#include "valhalla/worker.h"

#include "baldr/rapidjson_utils.h"

#include <gtest/gtest.h>

using namespace valhalla;

namespace {

constexpr double grid_size = 100;

// Build a map (A-B-C-D), BC carries the given nhvr_networks tag.
gurka::map build_linear_map(const std::string& test_nhvr_tag, const std::string& workdir) {
  const std::string ascii_map = R"(A---B---C---D)";
  const gurka::ways ways = {
      {"AB", {{"highway", "residential"}}},
      {"BC", {{"highway", "residential"}, {"nhvr_networks", test_nhvr_tag}}},
      {"CD", {{"highway", "residential"}}},
  };
  const auto layout = gurka::detail::map_to_coordinates(ascii_map, grid_size);
  return gurka::buildtiles(layout, ways, {}, {}, workdir);
}

} // namespace

TEST(NhvrTruck, ProhibitedNetworkBlocksEdge) {
  auto map = build_linear_map("NetA:2", "test/data/nhvr_prohibited");
  try {
    gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                     {{"/costing_options/truck/nhvr_networks/0", "NetA"}});
    FAIL() << "Expected no path to be found";
  } catch (const valhalla_exception_t& err) {
    EXPECT_EQ(err.code, 442);
  } catch (...) {
    FAIL() << "Expected valhalla_exception_t";
  }
}

TEST(NhvrTruck, NoNetworksRequestedRoutesNormally) {
  auto map = build_linear_map("NetA:2", "test/data/nhvr_no_request");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck");
  gurka::assert::raw::expect_path(res, {"AB", "BC", "CD"});
}

TEST(NhvrTruck, ApprovedNetworkAllowed) {
  auto map = build_linear_map("NetA:0", "test/data/nhvr_approved");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                              {{"/costing_options/truck/nhvr_networks/0", "NetA"}});
  gurka::assert::raw::expect_path(res, {"AB", "BC", "CD"});
}

TEST(NhvrTruck, ConditionalNetworkAllowed) {
  auto map = build_linear_map("NetA:1", "test/data/nhvr_conditional");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                              {{"/costing_options/truck/nhvr_networks/0", "NetA"}});
  gurka::assert::raw::expect_path(res, {"AB", "BC", "CD"});
}

TEST(NhvrTruck, UnrequestedNetworkIgnored) {
  auto map = build_linear_map("NetB:2", "test/data/nhvr_unrequested");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                              {{"/costing_options/truck/nhvr_networks/0", "NetA"}});
  gurka::assert::raw::expect_path(res, {"AB", "BC", "CD"});
}

TEST(NhvrTruck, MultipleNetworksOnEdge) {
  auto map = build_linear_map("NetA:0|NetB:2", "test/data/nhvr_multi");

  // approved on NetA, so requesting NetA is fine
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                              {{"/costing_options/truck/nhvr_networks/0", "NetA"}});
  gurka::assert::raw::expect_path(res, {"AB", "BC", "CD"});

  // prohibited on NetB, so requesting NetB blocks the edge
  try {
    gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                     {{"/costing_options/truck/nhvr_networks/0", "NetB"}});
    FAIL() << "Expected no path to be found";
  } catch (const valhalla_exception_t& err) {
    EXPECT_EQ(err.code, 442);
  }

  // requesting both networks also blocks the edge (NetB is prohibited)
  try {
    gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                     {{"/costing_options/truck/nhvr_networks/0", "NetA"},
                      {"/costing_options/truck/nhvr_networks/1", "NetB"}});
    FAIL() << "Expected no path to be found";
  } catch (const valhalla_exception_t& err) {
    EXPECT_EQ(err.code, 442);
  }
}

TEST(NhvrTruck, ReroutesAroundProhibitedEdge) {
  const std::string ascii_map = R"(
      A---B
      |   |
      C---D
  )";
  const gurka::ways ways = {
      {"AB", {{"highway", "residential"}, {"nhvr_networks", "NetA:2"}}},
      {"BD", {{"highway", "residential"}}},
      {"AC", {{"highway", "residential"}}},
      {"CD", {{"highway", "residential"}}},
  };
  const auto layout = gurka::detail::map_to_coordinates(ascii_map, grid_size);
  auto map = gurka::buildtiles(layout, ways, {}, {}, "test/data/nhvr_reroute");

  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                              {{"/costing_options/truck/nhvr_networks/0", "NetA"}});
  gurka::assert::raw::expect_path(res, {"AC", "CD"});
}

TEST(NhvrTruck, AutoCostingIgnoresNhvr) {
  auto map = build_linear_map("NetA:2", "test/data/nhvr_auto");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "auto");
  gurka::assert::raw::expect_path(res, {"AB", "BC", "CD"});
}

TEST(NhvrTruck, LongMotorwayRouteHonoursProhibitedEdge) {
  // Long routes use the hierarchy. Verify a prohibited edge in the middle of
  // a motorway chain still blocks the route.
  const std::string ascii_map =
      R"(A---B---C---D---E---F---G---H---I---J---K---L---M---N---O---P---Q---R---S---T)";
  gurka::ways ways;
  for (const auto& name : {"AB", "BC", "CD", "DE", "EF", "FG", "GH", "HI", "IJ", "JK", "KL",
                           "LM", "MN", "NO", "OP", "PQ", "QR", "RS", "ST"}) {
    ways[name] = {{"highway", "motorway"}};
  }
  ways["JK"] = {{"highway", "motorway"}, {"nhvr_networks", "NetA:2"}};

  // ~100 km total, so the route uses the hierarchy rather than local edges.
  const auto layout = gurka::detail::map_to_coordinates(ascii_map, 5000);
  auto map = gurka::buildtiles(layout, ways, {}, {}, "test/data/nhvr_shortcut");

  try {
    gurka::do_action(Options::route, map, {"A", "T"}, "truck",
                     {{"/costing_options/truck/nhvr_networks/0", "NetA"}});
    FAIL() << "Expected the prohibited edge to block the route";
  } catch (const valhalla_exception_t& err) {
    EXPECT_EQ(err.code, 442);
  }
}

TEST(NhvrSerialization, EdgeAttributePopulated) {
  auto map = build_linear_map("NetA:0|NetB:2", "test/data/nhvr_edge_attr");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                              {{"/filters/action", "include"},
                               {"/filters/attributes/0", "edge.nhvr_networks"}});

  const auto& leg = res.trip().routes(0).legs(0);
  ASSERT_EQ(leg.node(1).edge().nhvr_networks_size(), 2); // BC
  EXPECT_EQ(leg.node(1).edge().nhvr_networks(0).name(), "NetA");
  EXPECT_EQ(leg.node(1).edge().nhvr_networks(0).status(), "approved");
  EXPECT_EQ(leg.node(1).edge().nhvr_networks(1).name(), "NetB");
  EXPECT_EQ(leg.node(1).edge().nhvr_networks(1).status(), "prohibited");

  // untagged edges carry no networks
  EXPECT_EQ(leg.node(0).edge().nhvr_networks_size(), 0); // AB
  EXPECT_EQ(leg.node(2).edge().nhvr_networks_size(), 0); // CD
}

TEST(NhvrSerialization, EdgeAttributeConditionalStatus) {
  auto map = build_linear_map("NetA:1", "test/data/nhvr_edge_conditional");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck",
                              {{"/filters/action", "include"},
                               {"/filters/attributes/0", "edge.nhvr_networks"}});

  const auto& leg = res.trip().routes(0).legs(0);
  ASSERT_EQ(leg.node(1).edge().nhvr_networks_size(), 1); // BC
  EXPECT_EQ(leg.node(1).edge().nhvr_networks(0).name(), "NetA");
  EXPECT_EQ(leg.node(1).edge().nhvr_networks(0).status(), "conditional");
}

TEST(NhvrSerialization, EdgeAttributeOptInOnly) {
  auto map = build_linear_map("NetA:0|NetB:2", "test/data/nhvr_edge_optin");
  auto res = gurka::do_action(Options::route, map, {"A", "D"}, "truck");

  const auto& leg = res.trip().routes(0).legs(0);
  EXPECT_EQ(leg.node(1).edge().nhvr_networks_size(), 0); // BC
}

TEST(NhvrSerialization, ManeuverAggregationUsesMostRestrictiveStatus) {
  const std::string ascii_map = R"(A---B---C)";
  const gurka::ways ways = {
      {"AB", {{"highway", "residential"}, {"nhvr_networks", "NetA:0"}}},
      {"BC", {{"highway", "residential"}, {"nhvr_networks", "NetA:2"}}},
  };
  const auto layout = gurka::detail::map_to_coordinates(ascii_map, grid_size);
  auto map = gurka::buildtiles(layout, ways, {}, {}, "test/data/nhvr_aggregate");

  auto res = gurka::do_action(Options::route, map, {"A", "C"}, "truck",
                              {{"/filters/action", "include"},
                               {"/filters/attributes/0", "edge.nhvr_networks"}});

  // find the maneuver spanning both edges (start of a straight route)
  const auto& leg = res.directions().routes(0).legs(0);
  int spanning_idx = -1;
  for (int i = 0; i < leg.maneuver_size(); ++i) {
    if (leg.maneuver(i).end_path_index() - leg.maneuver(i).begin_path_index() >= 2) {
      spanning_idx = i;
    }
  }
  ASSERT_NE(spanning_idx, -1) << "expected a maneuver spanning both edges";

  auto d = gurka::convert_to_json(res, valhalla::Options_Format_json);
  const auto& m = d["trip"]["legs"][0]["maneuvers"][spanning_idx];
  ASSERT_TRUE(m.HasMember("nhvr_networks"));

  bool found = false;
  for (const auto& n : m["nhvr_networks"].GetArray()) {
    if (std::string(n["name"].GetString()) == "NetA") {
      EXPECT_EQ(std::string(n["status"].GetString()), "prohibited");
      found = true;
    }
  }
  EXPECT_TRUE(found);
}

TEST(NhvrSerialization, ManeuverAggregationApprovedAndConditional) {
  const std::string ascii_map = R"(A---B---C)";
  const gurka::ways ways = {
      {"AB", {{"highway", "residential"}, {"nhvr_networks", "NetA:0"}}},
      {"BC", {{"highway", "residential"}, {"nhvr_networks", "NetA:1"}}},
  };
  const auto layout = gurka::detail::map_to_coordinates(ascii_map, grid_size);
  auto map = gurka::buildtiles(layout, ways, {}, {}, "test/data/nhvr_aggregate_conditional");

  auto res = gurka::do_action(Options::route, map, {"A", "C"}, "truck",
                              {{"/filters/action", "include"},
                               {"/filters/attributes/0", "edge.nhvr_networks"}});

  // find the maneuver spanning both edges (start of a straight route)
  const auto& leg = res.directions().routes(0).legs(0);
  int spanning_idx = -1;
  for (int i = 0; i < leg.maneuver_size(); ++i) {
    if (leg.maneuver(i).end_path_index() - leg.maneuver(i).begin_path_index() >= 2) {
      spanning_idx = i;
    }
  }
  ASSERT_NE(spanning_idx, -1) << "expected a maneuver spanning both edges";

  auto d = gurka::convert_to_json(res, valhalla::Options_Format_json);
  const auto& m = d["trip"]["legs"][0]["maneuvers"][spanning_idx];
  ASSERT_TRUE(m.HasMember("nhvr_networks"));

  bool found = false;
  for (const auto& n : m["nhvr_networks"].GetArray()) {
    if (std::string(n["name"].GetString()) == "NetA") {
      EXPECT_EQ(std::string(n["status"].GetString()), "conditional");
      found = true;
    }
  }
  EXPECT_TRUE(found);
}

TEST(NhvrSerialization, ManeuverAggregationIncludesWayIds) {
  const std::string ascii_map = R"(A---B---C)";
  const gurka::ways ways = {
      {"AB", {{"highway", "residential"}, {"nhvr_networks", "NetA:0"}, {"osm_id", "100"}}},
      {"BC", {{"highway", "residential"}, {"nhvr_networks", "NetA:2"}, {"osm_id", "200"}}},
  };
  const auto layout = gurka::detail::map_to_coordinates(ascii_map, grid_size);
  auto map = gurka::buildtiles(layout, ways, {}, {}, "test/data/nhvr_way_ids");

  auto res = gurka::do_action(Options::route, map, {"A", "C"}, "truck",
                              {{"/filters/action", "include"},
                               {"/filters/attributes/0", "edge.nhvr_networks"},
                               {"/filters/attributes/1", "edge.way_id"}});

  // find the maneuver spanning both edges (start of a straight route)
  const auto& leg = res.directions().routes(0).legs(0);
  int spanning_idx = -1;
  for (int i = 0; i < leg.maneuver_size(); ++i) {
    if (leg.maneuver(i).end_path_index() - leg.maneuver(i).begin_path_index() >= 2) {
      spanning_idx = i;
    }
  }
  ASSERT_NE(spanning_idx, -1) << "expected a maneuver spanning both edges";

  auto d = gurka::convert_to_json(res, valhalla::Options_Format_json);
  const auto& m = d["trip"]["legs"][0]["maneuvers"][spanning_idx];
  ASSERT_TRUE(m.HasMember("nhvr_networks"));

  for (const auto& n : m["nhvr_networks"].GetArray()) {
    if (std::string(n["name"].GetString()) == "NetA") {
      EXPECT_EQ(std::string(n["status"].GetString()), "prohibited");
      ASSERT_TRUE(n.HasMember("way_ids"));
      const auto& way_ids = n["way_ids"].GetArray();
      ASSERT_EQ(way_ids.Size(), 2);
      EXPECT_EQ(way_ids[0].GetUint64(), 100);
      EXPECT_EQ(way_ids[1].GetUint64(), 200);
    }
  }
}
