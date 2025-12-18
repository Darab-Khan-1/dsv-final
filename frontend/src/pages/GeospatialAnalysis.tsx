import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout';
import { ChartCard, LoadingOverlay } from '@/components/common';
import { TaxiMap } from '@/components/maps/TaxiMap';
import { MapPin, Navigation, Layers } from 'lucide-react';
import { getPickupHotspots, getDropoffHotspots, getRoutePairs } from '@/api';
import type { Hotspot, RoutePair } from '@/api/types';

export default function GeospatialAnalysis() {
  const [showPickups, setShowPickups] = useState(true);
  const [showDropoffs, setShowDropoffs] = useState(true);

  const { data: pickupData, isLoading: pickupLoading } = useQuery({
    queryKey: ['pickupHotspots'],
    queryFn: () => getPickupHotspots({ top_n: 50, min_trips: 100 }),
    retry: 1,
  });

  const { data: dropoffData, isLoading: dropoffLoading } = useQuery({
    queryKey: ['dropoffHotspots'],
    queryFn: () => getDropoffHotspots({ top_n: 50, min_trips: 100 }),
    retry: 1,
  });

  const { data: routePairsData, isLoading: routesLoading } = useQuery({
    queryKey: ['routePairs'],
    queryFn: () => getRoutePairs(20),
    retry: 1,
  });

  const pickupHotspots = pickupData?.data ?? [];
  const dropoffHotspots = dropoffData?.data ?? [];
  const routePairs = routePairsData?.data ?? [];

  const parseRoutePair = (route: RoutePair) => {
    const pickupCoords = route.pickup.split(',').map(Number);
    const dropoffCoords = route.dropoff.split(',').map(Number);
    return {
      pickup: { lat: pickupCoords[0], lng: pickupCoords[1] },
      dropoff: { lat: dropoffCoords[0], lng: dropoffCoords[1] },
      trip_count: route.trip_count,
    };
  };
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Geospatial Analysis
          </h1>
          <p className="text-muted-foreground">
            Explore pickup and dropoff hotspots across NYC
          </p>
        </div>

        <div className="flex items-center gap-4 rounded-lg border border-border bg-secondary/30 p-4">
          <Layers className="h-5 w-5 text-muted-foreground" />
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showPickups}
                onChange={(e) => setShowPickups(e.target.checked)}
                className="rounded border-border"
              />
              <span className="text-sm text-foreground">Pickup Hotspots</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showDropoffs}
                onChange={(e) => setShowDropoffs(e.target.checked)}
                className="rounded border-border"
              />
              <span className="text-sm text-foreground">Dropoff Hotspots</span>
            </label>
          </div>
        </div>

        <ChartCard title="NYC Trip Heatmap" subtitle="Geographic distribution of taxi trips">
          {pickupLoading || dropoffLoading ? (
            <LoadingOverlay message="Loading map data..." />
          ) : (
            <TaxiMap
              pickupHotspots={pickupHotspots}
              dropoffHotspots={dropoffHotspots}
              showPickups={showPickups}
              showDropoffs={showDropoffs}
              height="500px"
            />
          )}
        </ChartCard>

        <div className="grid gap-6 lg:grid-cols-2">
          <ChartCard title="Top Pickup Locations" subtitle="Busiest pickup areas">
            {pickupLoading ? (
              <LoadingOverlay message="Loading pickup hotspots..." />
            ) : (
              <div className="space-y-3">
                {pickupHotspots.slice(0, 10).map((spot, i) => (
                  <div 
                    key={i}
                    className="flex items-center justify-between rounded-lg bg-secondary/50 p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-sm font-semibold text-primary">
                        {i + 1}
                      </div>
                      <div>
                        <p className="font-medium text-foreground">
                          {spot.latitude.toFixed(4)}, {spot.longitude.toFixed(4)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Grid location
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-primary">{spot.trip_count.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">trips</p>
                    </div>
                  </div>
                ))}
                {pickupHotspots.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No pickup hotspots found
                  </p>
                )}
              </div>
            )}
          </ChartCard>

          <ChartCard title="Top Dropoff Locations" subtitle="Common destination areas">
            {dropoffLoading ? (
              <LoadingOverlay message="Loading dropoff hotspots..." />
            ) : (
              <div className="space-y-3">
                {dropoffHotspots.slice(0, 10).map((spot, i) => (
                  <div 
                    key={i}
                    className="flex items-center justify-between rounded-lg bg-secondary/50 p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-chart-2/20 text-sm font-semibold text-chart-2">
                        {i + 1}
                      </div>
                      <div>
                        <p className="font-medium text-foreground">
                          {spot.latitude.toFixed(4)}, {spot.longitude.toFixed(4)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Grid location
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-chart-2">{spot.trip_count.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">trips</p>
                    </div>
                  </div>
                ))}
                {dropoffHotspots.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No dropoff hotspots found
                  </p>
                )}
              </div>
            )}
          </ChartCard>
        </div>

        <ChartCard title="Popular Routes" subtitle="Most common pickup to dropoff pairs">
          {routesLoading ? (
            <LoadingOverlay message="Loading route pairs..." />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {routePairs.slice(0, 12).map((route, i) => {
                const parsed = parseRoutePair(route);
                return (
                  <div 
                    key={i}
                    className="flex items-center gap-3 rounded-lg border border-border bg-secondary/30 p-4"
                  >
                    <Navigation className="h-5 w-5 text-primary shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-foreground">
                        <span className="font-medium">
                          {parsed.pickup.lat.toFixed(2)}, {parsed.pickup.lng.toFixed(2)}
                        </span>
                        <span className="mx-2 text-muted-foreground">→</span>
                        <span className="font-medium">
                          {parsed.dropoff.lat.toFixed(2)}, {parsed.dropoff.lng.toFixed(2)}
                        </span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {parsed.trip_count.toLocaleString()} trips
                      </p>
                    </div>
                  </div>
                );
              })}
              {routePairs.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4 col-span-full">
                  No route pairs found
                </p>
              )}
            </div>
          )}
        </ChartCard>
      </div>
    </DashboardLayout>
  );
}
