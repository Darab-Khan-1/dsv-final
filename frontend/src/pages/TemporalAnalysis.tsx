import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout';
import { ChartCard, LoadingOverlay, ErrorDisplay } from '@/components/common';
import { LineChart, BarChart, AreaChart } from '@/components/charts';
import { getTripsByHour, getTripsByDay, getTripsByMonth, getFareTrends } from '@/api';
import { Button } from '@/components/ui/button';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export default function TemporalAnalysis() {
  const [yearFilter, setYearFilter] = useState<string>('all');
  const [monthFilter, setMonthFilter] = useState<string>('all');

  const year = yearFilter !== 'all' ? parseInt(yearFilter) : undefined;
  const month = monthFilter !== 'all' ? parseInt(monthFilter) : undefined;

  const { data: hourlyData, isLoading: hourlyLoading, error: hourlyError } = useQuery({
    queryKey: ['tripsByHour', year, month],
    queryFn: () => getTripsByHour({ year, month }),
    retry: 1,
  });

  const { data: dailyData, isLoading: dailyLoading } = useQuery({
    queryKey: ['tripsByDay', year, month],
    queryFn: () => getTripsByDay({ year, month }),
    retry: 1,
  });

  const { data: monthlyData, isLoading: monthlyLoading } = useQuery({
    queryKey: ['tripsByMonth', year],
    queryFn: () => getTripsByMonth({ year }),
    retry: 1,
  });

  const { data: fareTrends, isLoading: fareLoading } = useQuery({
    queryKey: ['fareTrends', year],
    queryFn: () => getFareTrends({ group_by: 'hour', year }),
    retry: 1,
  });

  // Process real API data
  const hourlyChartData = hourlyData?.data?.map(d => ({
    hour: `${d.hour}:00`,
    trip_count: d.trip_count
  })) ?? [];

  const dailyChartData = dailyData?.data?.map(d => ({
    day: dayNames[d.day_of_week - 1] || String(d.day_of_week),
    trip_count: d.trip_count
  })) ?? [];

  const monthlyChartData = monthlyData?.data?.map(d => ({
    month: monthNames[d.month - 1] || String(d.month),
    trip_count: d.trip_count
  })) ?? [];

  const fareChartData = fareTrends?.data?.map(d => ({
    hour: `${d.hour}:00`,
    avg_fare: d.avg_fare
  })) ?? [];

  // Calculate insights from real data
  const busiestHour = hourlyData?.data?.length 
    ? hourlyData.data.reduce((max, d) => d.trip_count > max.trip_count ? d : max)
    : null;
  const quietestHour = hourlyData?.data?.length
    ? hourlyData.data.reduce((min, d) => d.trip_count < min.trip_count ? d : min)
    : null;

  const peakDay = dailyData?.data?.length
    ? dailyData.data.reduce((max, d) => d.trip_count > max.trip_count ? d : max)
    : null;
  const lowestDay = dailyData?.data?.length
    ? dailyData.data.reduce((min, d) => d.trip_count < min.trip_count ? d : min)
    : null;

  // Format hour for display (convert 24-hour to 12-hour with AM/PM)
  const formatHour = (hour: number): string => {
    if (hour === 0) return '12:00 AM';
    if (hour < 12) return `${hour}:00 AM`;
    if (hour === 12) return '12:00 PM';
    return `${hour - 12}:00 PM`;
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Temporal Analysis
            </h1>
            <p className="text-muted-foreground">
              Explore trip patterns across time
            </p>
          </div>

          {/* Filters */}
          <div className="flex gap-3">
            <Select value={yearFilter} onValueChange={setYearFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Years</SelectItem>
                <SelectItem value="2015">2015</SelectItem>
                <SelectItem value="2016">2016</SelectItem>
              </SelectContent>
            </Select>

            <Select value={monthFilter} onValueChange={setMonthFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Month" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Months</SelectItem>
                {monthNames.map((name, i) => (
                  <SelectItem key={i} value={String(i + 1)}>{name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          <ChartCard 
            title="Trips by Hour of Day" 
            subtitle="24-hour demand pattern"
          >
            {hourlyLoading ? (
              <LoadingOverlay message="Loading hourly data..." />
            ) : (
              <AreaChart 
                data={hourlyChartData} 
                xKey="hour" 
                yKey="trip_count"
                height={300}
              />
            )}
          </ChartCard>

          <ChartCard 
            title="Trips by Day of Week" 
            subtitle="Weekly pattern analysis"
          >
            {dailyLoading ? (
              <LoadingOverlay message="Loading daily data..." />
            ) : (
              <BarChart 
                data={dailyChartData}
                xKey="day"
                yKey="trip_count"
                height={300}
              />
            )}
          </ChartCard>

          <ChartCard 
            title="Monthly Trip Volume" 
            subtitle="Seasonal trends"
          >
            {monthlyLoading ? (
              <LoadingOverlay message="Loading monthly data..." />
            ) : (
              <LineChart 
                data={monthlyChartData}
                xKey="month"
                yKey="trip_count"
                height={300}
              />
            )}
          </ChartCard>

          <ChartCard 
            title="Average Fare by Hour" 
            subtitle="Fare patterns throughout the day"
          >
            {fareLoading ? (
              <LoadingOverlay message="Loading fare data..." />
            ) : (
              <LineChart 
                data={fareChartData}
                xKey="hour"
                yKey="avg_fare"
                height={300}
                colors={['hsl(45, 93%, 58%)']}
              />
            )}
          </ChartCard>
        </div>

        {/* Insights */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="mb-4 text-lg font-semibold text-foreground">Key Insights</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg bg-secondary/50 p-4">
              <p className="text-sm text-muted-foreground">Busiest Hour</p>
              <p className="text-2xl font-bold text-primary">
                {busiestHour ? formatHour(busiestHour.hour) : 'N/A'}
              </p>
              {busiestHour && (
                <p className="text-xs text-muted-foreground mt-1">
                  {busiestHour.trip_count.toLocaleString()} trips
                </p>
              )}
            </div>
            <div className="rounded-lg bg-secondary/50 p-4">
              <p className="text-sm text-muted-foreground">Quietest Hour</p>
              <p className="text-2xl font-bold text-foreground">
                {quietestHour ? formatHour(quietestHour.hour) : 'N/A'}
              </p>
              {quietestHour && (
                <p className="text-xs text-muted-foreground mt-1">
                  {quietestHour.trip_count.toLocaleString()} trips
                </p>
              )}
            </div>
            <div className="rounded-lg bg-secondary/50 p-4">
              <p className="text-sm text-muted-foreground">Peak Day</p>
              <p className="text-2xl font-bold text-chart-4">
                {peakDay 
                  ? dayNames[peakDay.day_of_week - 1] || `Day ${peakDay.day_of_week}`
                  : 'N/A'}
              </p>
              {peakDay && (
                <p className="text-xs text-muted-foreground mt-1">
                  {peakDay.trip_count.toLocaleString()} trips
                </p>
              )}
            </div>
            <div className="rounded-lg bg-secondary/50 p-4">
              <p className="text-sm text-muted-foreground">Lowest Day</p>
              <p className="text-2xl font-bold text-foreground">
                {lowestDay
                  ? dayNames[lowestDay.day_of_week - 1] || `Day ${lowestDay.day_of_week}`
                  : 'N/A'}
              </p>
              {lowestDay && (
                <p className="text-xs text-muted-foreground mt-1">
                  {lowestDay.trip_count.toLocaleString()} trips
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
