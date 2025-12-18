import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout';
import { ChartCard, LoadingOverlay, StatCard } from '@/components/common';
import { BarChart, HorizontalBarChart } from '@/components/charts';
import { getPriceElasticity, getMarketShare, getSurgePricing, getDataSummary, getEconomicInsights } from '@/api';
import { getDateRange } from '@/api/endpoints/data';
import { DollarSign, TrendingUp, PieChart as PieChartIcon, BarChart3 } from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend, BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const COLORS = ['hsl(187, 85%, 53%)', 'hsl(280, 65%, 60%)', 'hsl(45, 93%, 58%)', 'hsl(142, 70%, 45%)'];

export default function EconomicAnalysis() {
  const { data: priceData, isLoading: priceLoading } = useQuery({
    queryKey: ['priceElasticity'],
    queryFn: getPriceElasticity,
    retry: 1,
  });

  const { data: marketData, isLoading: marketLoading } = useQuery({
    queryKey: ['marketShare'],
    queryFn: getMarketShare,
    retry: 1,
  });

  const { data: surgeData, isLoading: surgeLoading } = useQuery({
    queryKey: ['surgePricing'],
    queryFn: () => getSurgePricing(3.0),
    retry: 1,
  });

  const { data: dateRange } = useQuery({
    queryKey: ['dateRange'],
    queryFn: getDateRange,
    retry: 1,
  });

  const { data: summaryData } = useQuery({
    queryKey: ['dataSummary'],
    queryFn: getDataSummary,
    retry: 1,
  });

  const { data: insightsData, isLoading: insightsLoading } = useQuery({
    queryKey: ['economicInsights'],
    queryFn: getEconomicInsights,
    retry: 1,
  });

  const priceElasticity = priceData?.data || [];
  const marketShare = marketData?.data || [];
  const formatRevenue = (revenue: number) => {
    if (revenue >= 1_000_000_000) {
      return `$${(revenue / 1_000_000_000).toFixed(1)}B`;
    } else if (revenue >= 1_000_000) {
      return `$${(revenue / 1_000_000).toFixed(1)}M`;
    } else if (revenue >= 1_000) {
      return `$${(revenue / 1_000).toFixed(1)}K`;
    }
    return `$${revenue.toFixed(2)}`;
  };

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const totalRevenue = summaryData?.economic_metrics?.total_revenue 
    ? formatRevenue(summaryData.economic_metrics.total_revenue)
    : 'N/A';
  
  const avgFarePerMile = summaryData?.economic_metrics?.avg_fare_per_mile
    ? formatCurrency(summaryData.economic_metrics.avg_fare_per_mile)
    : 'N/A';
  
  const tipRate = summaryData?.economic_metrics?.avg_tip_rate
    ? formatPercentage(summaryData.economic_metrics.avg_tip_rate)
    : 'N/A';
  const calculateMonthlyAverage = () => {
    if (!surgeData?.total_surge_events || !dateRange) return 'N/A';
    
    const startDate = new Date(dateRange.min_date);
    const endDate = new Date(dateRange.max_date);
    const monthsDiff = (endDate.getFullYear() - startDate.getFullYear()) * 12 + 
                      (endDate.getMonth() - startDate.getMonth()) + 1;
    
    if (monthsDiff <= 0) return 'N/A';
    
    const monthlyAvg = surgeData.total_surge_events / monthsDiff;
    
    if (monthlyAvg >= 1000) {
      return `${(monthlyAvg / 1000).toFixed(1)}K`;
    }
    return Math.round(monthlyAvg).toLocaleString();
  };

  const monthlySurgeAverage = calculateMonthlyAverage();

  const pieData = marketShare.map((item) => ({
    name: `Vendor ${item.vendor_id}`,
    value: item.market_share_percent,
    trips: item.trip_count,
    avgFare: item.avg_fare,
  }));

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Economic Analysis
          </h1>
          <p className="text-muted-foreground">
            Revenue, pricing, and market insights
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Revenue"
            value={totalRevenue}
            subtitle="All time"
            icon={DollarSign}
            variant="primary"
          />
          <StatCard
            title="Avg Fare/Mile"
            value={avgFarePerMile}
            subtitle="Average fare per mile"
            icon={TrendingUp}
          />
          <StatCard
            title="Tip Rate"
            value={tipRate}
            subtitle="Average tip percentage"
            icon={PieChartIcon}
          />
          <StatCard
            title="Surge Events"
            value={surgeLoading ? "..." : monthlySurgeAverage}
            subtitle={`Per month average (z-score > 3.0)`}
            icon={BarChart3}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <ChartCard 
            title="Fare per Mile by Distance" 
            subtitle="Average fare per mile (not total fare) - shorter trips have higher per-mile rates due to base fares"
          >
            {priceLoading ? (
              <LoadingOverlay message="Loading price data..." />
            ) : priceElasticity.length === 0 ? (
              <div className="flex items-center justify-center h-[280px] text-muted-foreground">
                <p>No price elasticity data available</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <RechartsBarChart 
                  data={priceElasticity
                    .sort((a, b) => {
                      const order = { 'Short': 1, 'Medium': 2, 'Long': 3, 'Very Long': 4 };
                      const aOrder = order[a.distance_bucket.split(' ')[0] as keyof typeof order] || 0;
                      const bOrder = order[b.distance_bucket.split(' ')[0] as keyof typeof order] || 0;
                      return aOrder - bOrder;
                    })
                    .map(d => ({
                      distance: d.distance_bucket,
                      farePerMile: d.avg_fare_per_mile,
                      avgFare: d.avg_fare,
                      avgDistance: d.avg_distance,
                      tripCount: d.trip_count
                    }))}
                  layout="vertical" 
                  margin={{ top: 10, right: 30, left: 100, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 30%, 18%)" horizontal={false} />
                  <XAxis 
                    type="number"
                    stroke="hsl(215, 20%, 55%)" 
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
                    label={{ value: 'Fare per Mile ($)', position: 'insideBottom', offset: -5, style: { fill: 'hsl(215, 20%, 55%)' } }}
                    tickFormatter={(value) => `$${value.toFixed(2)}`}
                  />
                  <YAxis 
                    type="category"
                    dataKey="distance"
                    stroke="hsl(215, 20%, 55%)" 
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
                    width={95}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(222, 47%, 8%)', 
                      border: '1px solid hsl(222, 30%, 18%)',
                      borderRadius: '8px',
                      color: 'hsl(210, 40%, 98%)'
                    }}
                    cursor={{ fill: 'hsl(222, 30%, 15%)' }}
                    formatter={(value: number) => `$${value.toFixed(2)}/mile`}
                    labelFormatter={(label) => `${label}`}
                  />
                  <Bar dataKey="farePerMile" radius={[0, 4, 4, 0]}>
                    {priceElasticity.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={['hsl(187, 85%, 53%)', 'hsl(200, 80%, 50%)', 'hsl(187, 85%, 43%)', 'hsl(187, 75%, 40%)'][index % 4]} />
                    ))}
                  </Bar>
                </RechartsBarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard 
            title="Vendor Market Share" 
            subtitle="Trip distribution by vendor"
          >
            {marketLoading ? (
              <LoadingOverlay message="Loading market data..." />
            ) : marketShare.length === 0 ? (
              <div className="flex items-center justify-center h-[280px] text-muted-foreground">
                <p>No market share data available</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(222, 47%, 8%)', 
                      border: '1px solid hsl(222, 30%, 18%)',
                      borderRadius: '8px',
                      color: 'hsl(210, 40%, 98%)'
                    }}
                    formatter={(value: number) => [`${value.toFixed(1)}%`, 'Market Share']}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Highest Tip Hour</p>
            {insightsLoading ? (
              <p className="text-2xl font-bold text-chart-3">...</p>
            ) : (
              <p className="text-2xl font-bold text-chart-3">
                {insightsData?.highest_tip_hour !== null && insightsData?.highest_tip_hour !== undefined
                  ? (() => {
                      const hour = insightsData.highest_tip_hour!;
                      const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
                      const period = hour >= 12 ? 'PM' : 'AM';
                      return `${displayHour}:00 ${period}`;
                    })()
                  : 'N/A'}
              </p>
            )}
            <p className="text-xs text-muted-foreground">Late night passengers tip more</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Best Revenue Hour</p>
            {insightsLoading ? (
              <p className="text-2xl font-bold text-chart-4">...</p>
            ) : (
              <p className="text-2xl font-bold text-chart-4">
                {insightsData?.best_revenue_hour !== null && insightsData?.best_revenue_hour !== undefined
                  ? (() => {
                      const hour = insightsData.best_revenue_hour!;
                      const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
                      const period = hour >= 12 ? 'PM' : 'AM';
                      return `${displayHour}:00 ${period}`;
                    })()
                  : 'N/A'}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              {insightsData?.best_revenue_hour !== null && insightsData?.best_revenue_hour !== undefined
                ? (() => {
                    const hour = insightsData.best_revenue_hour!;
                    if ((hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 19)) {
                      return 'Rush hour premium pricing';
                    } else if (hour >= 22 || hour <= 6) {
                      return 'Late night / early morning premium';
                    } else {
                      return 'Hour with highest average fare';
                    }
                  })()
                : 'Hour with highest average fare'}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Airport Premium</p>
            {insightsLoading ? (
              <p className="text-2xl font-bold text-primary">...</p>
            ) : (
              <p className="text-2xl font-bold text-primary">
                {insightsData?.airport_premium !== undefined
                  ? `${insightsData.airport_premium >= 0 ? '+' : ''}${insightsData.airport_premium.toFixed(1)}%`
                  : 'N/A'}
              </p>
            )}
            <p className="text-xs text-muted-foreground">vs city average fare</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Credit Card Tip</p>
            {insightsLoading ? (
              <p className="text-2xl font-bold text-chart-2">...</p>
            ) : (
              <p className="text-2xl font-bold text-chart-2">
                {insightsData?.credit_card_tip_premium !== undefined
                  ? `${insightsData.credit_card_tip_premium >= 0 ? '+' : ''}${insightsData.credit_card_tip_premium.toFixed(1)}%`
                  : 'N/A'}
              </p>
            )}
            <p className="text-xs text-muted-foreground">Higher than cash tips</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
