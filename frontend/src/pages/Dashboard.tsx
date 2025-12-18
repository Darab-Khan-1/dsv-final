import { useQuery } from '@tanstack/react-query';
import { 
  Car, 
  DollarSign, 
  Clock, 
  TrendingUp,
  MapPin,
  Users
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout';
import { StatCard, ChartCard, LoadingOverlay, ErrorDisplay } from '@/components/common';
import { AreaChart, BarChart, HorizontalBarChart } from '@/components/charts';
import { getDataSummary, getTripsByHour, getTripsByDay, getPeakHours } from '@/api';

const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ['dataSummary'],
    queryFn: getDataSummary,
    retry: 1,
  });

  const { data: hourlyData, isLoading: hourlyLoading } = useQuery({
    queryKey: ['tripsByHour'],
    queryFn: () => getTripsByHour(),
    retry: 1,
  });

  const { data: dailyData, isLoading: dailyLoading } = useQuery({
    queryKey: ['tripsByDay'],
    queryFn: () => getTripsByDay(),
    retry: 1,
  });

  const { data: peakHoursData, isLoading: peakLoading } = useQuery({
    queryKey: ['peakHours'],
    queryFn: () => getPeakHours(5),
    retry: 1,
  });

  const hourlyChartData = hourlyData?.data ?? [];
  const dailyChartData =
    dailyData?.data?.map(d => ({
      day: dayNames[d.day_of_week - 1] || String(d.day_of_week),
      trip_count: d.trip_count,
    })) ?? [];
  const peakHoursChartData =
    peakHoursData?.data?.map(d => ({
      hour: `${d.hour}:00`,
      trip_count: d.trip_count,
    })) ?? [];

  const totalTrips = summary?.total_records ?? 0;
  const avgFare = summary?.summary?.mean?.fare_amount ?? 0;
  const avgDistance = summary?.summary?.mean?.trip_distance ?? 0;
  const avgDuration = summary?.summary?.mean?.trip_duration_minutes ?? 0;
  const peakDay =
    dailyChartData.length > 0
      ? dailyChartData.reduce((max, d) => (d.trip_count > max.trip_count ? d : max))
          .day
      : 'N/A';
  const rushHour =
    peakHoursChartData.length > 0 ? peakHoursChartData[0].hour : 'N/A';
  const avgTipPercent =
    summary && summary.summary?.mean?.tip_amount && summary.summary?.mean?.fare_amount
      ? (summary.summary.mean.tip_amount / summary.summary.mean.fare_amount) * 100
      : 0;
  const avgPassengers = summary?.summary?.mean?.passenger_count ?? 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            NYC Taxi Analytics
          </h1>
          <p className="text-muted-foreground">
            Real-time insights into New York City taxi operations
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Trips"
            value={totalTrips.toLocaleString()}
            subtitle="All time records"
            icon={Car}
            variant="primary"
          />
          <StatCard
            title="Average Fare"
            value={`$${avgFare.toFixed(2)}`}
            subtitle="Per trip"
            icon={DollarSign}
          />
          <StatCard
            title="Avg Distance"
            value={`${avgDistance.toFixed(1)} mi`}
            subtitle="Per trip"
            icon={MapPin}
          />
          <StatCard
            title="Avg Duration"
            value={`${avgDuration.toFixed(0)} min`}
            subtitle="Per trip"
            icon={Clock}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <ChartCard 
            title="Trips by Hour" 
            subtitle="24-hour distribution"
            className="lg:col-span-2"
          >
            {hourlyLoading ? (
              <LoadingOverlay message="Loading hourly data..." />
            ) : (
              <AreaChart 
                data={hourlyChartData} 
                xKey="hour" 
                yKey="trip_count"
                height={280}
              />
            )}
          </ChartCard>

          <ChartCard title="Peak Hours" subtitle="Top 5 busiest hours">
            {peakLoading ? (
              <LoadingOverlay message="Loading peak hours..." />
            ) : (
              <HorizontalBarChart 
                data={peakHoursChartData}
                nameKey="hour"
                valueKey="trip_count"
                height={280}
              />
            )}
          </ChartCard>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <ChartCard title="Trips by Day" subtitle="Weekly pattern">
            {dailyLoading ? (
              <LoadingOverlay message="Loading daily data..." />
            ) : (
              <BarChart 
                data={dailyChartData}
                xKey="day"
                yKey="trip_count"
                height={280}
              />
            )}
          </ChartCard>

          <ChartCard title="Quick Insights" subtitle="Key metrics">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg bg-secondary/50 p-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-chart-1/10 p-2">
                    <TrendingUp className="h-5 w-5 text-chart-1" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Peak Day</p>
                    <p className="text-lg font-semibold text-foreground">{peakDay}</p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg bg-secondary/50 p-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-chart-2/10 p-2">
                    <Clock className="h-5 w-5 text-chart-2" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Rush Hour</p>
                    <p className="text-lg font-semibold text-foreground">{rushHour}</p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg bg-secondary/50 p-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-chart-3/10 p-2">
                    <DollarSign className="h-5 w-5 text-chart-3" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Tip</p>
                    <p className="text-lg font-semibold text-foreground">
                      {avgTipPercent ? `${avgTipPercent.toFixed(1)}%` : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="rounded-lg bg-secondary/50 p-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-chart-4/10 p-2">
                    <Users className="h-5 w-5 text-chart-4" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Passengers</p>
                    <p className="text-lg font-semibold text-foreground">
                      {avgPassengers ? avgPassengers.toFixed(1) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </ChartCard>
        </div>

        {summaryError && (
          <div className="rounded-lg border border-chart-3/30 bg-chart-3/10 p-4">
            <p className="text-sm text-chart-3">
              <strong>Note:</strong> {
                (summaryError as any)?.isConnectionError 
                  ? "Unable to connect to the API at localhost:8000. Start your backend server to see live data."
                  : "API returned an error. This may be due to missing dependencies (PySpark). Displaying sample data."
              }
            </p>
            {(summaryError as any)?.response && (
              <p className="text-xs text-chart-3/70 mt-2">
                Error: {(summaryError as any).response?.data?.detail || (summaryError as any).message}
              </p>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
