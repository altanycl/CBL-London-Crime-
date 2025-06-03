"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import FilterPanel from "@/components/filter-panel";
import PastBurglariesMap from "@/components/past-burglaries-map";
import PredictedBurglariesMap from "@/components/predicted-burglaries-map";
import PredictionMetrics from "@/components/prediction-metrics";
import PoliceAllocation from "@/components/police-allocation";
import PopoutButton from "@/components/popout-button";

const Dashboard = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Left Column */}
      <div className="lg:col-span-1 space-y-6">
        <Card className="bg-sky-50 shadow-lg rounded-3xl border-2">
          <CardHeader>
            <CardTitle className="text-center">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <FilterPanel />
          </CardContent>
        </Card>

        <Card className="bg-sky-50 shadow-lg rounded-3xl border-2">
          <CardHeader>
            <CardTitle className="text-center">Police Allocation</CardTitle>
          </CardHeader>
          <CardContent>
            <PoliceAllocation />
          </CardContent>
        </Card>
      </div>

      {/* Right Column */}
      <div className="lg:col-span-3 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Past Burglaries Map */}
          <Card className="bg-sky-50 shadow-lg rounded-3xl border-2">
            <CardHeader>
              <CardTitle className="text-center">London Choropleth Map - Past Burglaries</CardTitle>
            </CardHeader>
            <CardContent>
              <PastBurglariesMap />
            </CardContent>
          </Card>

          {/* Predicted Burglaries Map */}
          <Card className="bg-sky-50 shadow-lg rounded-3xl border-2">
            <CardHeader>
              <CardTitle className="text-center">London Map - Predicted Burglaries</CardTitle>
            </CardHeader>
            <CardContent>
              <PredictedBurglariesMap />
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* All Popouts in one card */}
          <Card className="bg-sky-50 shadow-lg rounded-3xl border-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-center">Interactive Reports</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-3">
              <PopoutButton text="Popout for Explainability Report" title="Model Explainability Report" />
              <PopoutButton text="Popout for Fairness Check" title="Model Fairness Analysis" />
              <PopoutButton text="Popout for Duty Sheet" title="Police Duty Sheet & Allocations" />
            </CardContent>
          </Card>

          {/* Prediction Metrics */}
          <Card className="bg-sky-50 shadow-lg rounded-3xl border-2">
            <CardHeader>
              <CardTitle className="text-center">Prediction Metrics and other stats</CardTitle>
            </CardHeader>
            <CardContent>
              <PredictionMetrics />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 