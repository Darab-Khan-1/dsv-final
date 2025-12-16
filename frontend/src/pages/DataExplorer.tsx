import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout';
import { ChartCard, LoadingOverlay, StatCard } from '@/components/common';
import { getDataSummary, getDateRange, getPaginatedData } from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Database, Download, RefreshCw, Calendar, Hash, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Filter, X } from 'lucide-react';
import type { TripRecord } from '@/api/types';

interface FilterState {
  year: string;
  month: string;
  payment_type: string;
  min_fare: string;
  max_fare: string;
  min_distance: string;
  max_distance: string;
  min_passengers: string;
  max_passengers: string;
}

export default function DataExplorer() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  const [orderBy, setOrderBy] = useState<string>('tpep_pickup_datetime');
  const [orderDirection, setOrderDirection] = useState<'asc' | 'desc'>('asc');
  const [filtersApplied, setFiltersApplied] = useState(false);
  const [isFiltersOpen, setIsFiltersOpen] = useState(true);
  
  // Filter state (not applied until user clicks "Apply Filters")
  const [filters, setFilters] = useState<FilterState>({
    year: 'all',
    month: 'all',
    payment_type: 'all',
    min_fare: '',
    max_fare: '',
    min_distance: '',
    max_distance: '',
    min_passengers: '',
    max_passengers: '',
  });

  // Applied filters (used for query)
  const [appliedFilters, setAppliedFilters] = useState<FilterState>({
    year: 'all',
    month: 'all',
    payment_type: 'all',
    min_fare: '',
    max_fare: '',
    min_distance: '',
    max_distance: '',
    min_passengers: '',
    max_passengers: '',
  });

  // Convert filters to API params
  const getQueryParams = () => {
    const params: any = {
      page,
      page_size: pageSize,
      order_by: orderBy,
      order_direction: orderDirection,
    };

    if (appliedFilters.year !== 'all') params.year = parseInt(appliedFilters.year);
    if (appliedFilters.month !== 'all') params.month = parseInt(appliedFilters.month);
    if (appliedFilters.payment_type !== 'all') params.payment_type = parseInt(appliedFilters.payment_type);
    if (appliedFilters.min_fare) params.min_fare = parseFloat(appliedFilters.min_fare);
    if (appliedFilters.max_fare) params.max_fare = parseFloat(appliedFilters.max_fare);
    if (appliedFilters.min_distance) params.min_distance = parseFloat(appliedFilters.min_distance);
    if (appliedFilters.max_distance) params.max_distance = parseFloat(appliedFilters.max_distance);
    if (appliedFilters.min_passengers) params.min_passengers = parseInt(appliedFilters.min_passengers);
    if (appliedFilters.max_passengers) params.max_passengers = parseInt(appliedFilters.max_passengers);

    return params;
  };

  const handleApplyFilters = () => {
    setAppliedFilters({ ...filters });
    setFiltersApplied(true);
    setPage(1); // Reset to first page
  };

  const handleClearFilters = () => {
    const emptyFilters: FilterState = {
      year: 'all',
      month: 'all',
      payment_type: 'all',
      min_fare: '',
      max_fare: '',
      min_distance: '',
      max_distance: '',
      min_passengers: '',
      max_passengers: '',
    };
    setFilters(emptyFilters);
    setAppliedFilters(emptyFilters);
    setFiltersApplied(false);
    setPage(1);
  };

  const hasActiveFilters = () => {
    return appliedFilters.year !== 'all' ||
           appliedFilters.month !== 'all' ||
           appliedFilters.payment_type !== 'all' ||
           appliedFilters.min_fare !== '' ||
           appliedFilters.max_fare !== '' ||
           appliedFilters.min_distance !== '' ||
           appliedFilters.max_distance !== '' ||
           appliedFilters.min_passengers !== '' ||
           appliedFilters.max_passengers !== '';
  };

  const { data: summary } = useQuery({
    queryKey: ['dataSummary'],
    queryFn: getDataSummary,
    retry: 1,
  });

  const { data: dateRange } = useQuery({
    queryKey: ['dateRange'],
    queryFn: getDateRange,
    retry: 1,
  });

  // Only fetch data if filters are applied
  const { data: paginatedData, isLoading, refetch } = useQuery({
    queryKey: ['paginatedData', ...Object.values(getQueryParams())],
    queryFn: () => getPaginatedData(getQueryParams()),
    retry: 1,
    keepPreviousData: true,
    enabled: filtersApplied || hasActiveFilters(), // Only fetch when filters are applied
  });

  const records = paginatedData?.data || [];
  const pagination = paginatedData?.pagination;
  const totalRecords = pagination?.total_count || summary?.total_records || 0;
  const minDate = dateRange?.min_date || '2015-01-01';
  const maxDate = dateRange?.max_date || '2016-03-31';

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const handleExport = () => {
    if (records.length === 0) return;
    
    const csv = [
      Object.keys(records[0]).join(','),
      ...records.map(r => Object.values(r).map(v => {
        if (v === null || v === undefined) return '';
        if (typeof v === 'string' && v.includes(',')) return `"${v}"`;
        return String(v);
      }).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `taxi_data_page_${page}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Data Explorer
            </h1>
            <p className="text-muted-foreground">
              Browse trip data with advanced filtering and pagination
            </p>
          </div>
          <div className="flex gap-2">
            <Select value={pageSize.toString()} onValueChange={(value) => { setPageSize(parseInt(value)); setPage(1); }}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Page Size" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="50">50 rows</SelectItem>
                <SelectItem value="100">100 rows</SelectItem>
                <SelectItem value="250">250 rows</SelectItem>
                <SelectItem value="500">500 rows</SelectItem>
                <SelectItem value="1000">1000 rows</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="icon" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button variant="outline" onClick={handleExport} className="gap-2" disabled={records.length === 0}>
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Filters Panel */}
        <Collapsible open={isFiltersOpen} onOpenChange={setIsFiltersOpen}>
          <ChartCard 
            title={
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  <span>Filters</span>
                  {hasActiveFilters() && (
                    <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
                      Active
                    </span>
                  )}
                </div>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm">
                    {isFiltersOpen ? 'Hide' : 'Show'} Filters
                  </Button>
                </CollapsibleTrigger>
              </div>
            }
          >
            <CollapsibleContent>
              <div className="space-y-4 pt-4">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {/* Year Filter */}
                  <div className="space-y-2">
                    <Label htmlFor="year">Year</Label>
                    <Select value={filters.year} onValueChange={(value) => setFilters({ ...filters, year: value })}>
                      <SelectTrigger id="year">
                        <SelectValue placeholder="All Years" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Years</SelectItem>
                        <SelectItem value="2015">2015</SelectItem>
                        <SelectItem value="2016">2016</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Month Filter */}
                  <div className="space-y-2">
                    <Label htmlFor="month">Month</Label>
                    <Select value={filters.month} onValueChange={(value) => setFilters({ ...filters, month: value })}>
                      <SelectTrigger id="month">
                        <SelectValue placeholder="All Months" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Months</SelectItem>
                        {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                          <SelectItem key={m} value={m.toString()}>
                            {new Date(2016, m - 1).toLocaleString('default', { month: 'long' })}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Payment Type Filter */}
                  <div className="space-y-2">
                    <Label htmlFor="payment_type">Payment Type</Label>
                    <Select value={filters.payment_type} onValueChange={(value) => setFilters({ ...filters, payment_type: value })}>
                      <SelectTrigger id="payment_type">
                        <SelectValue placeholder="All Types" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        <SelectItem value="1">Card</SelectItem>
                        <SelectItem value="2">Cash</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Passenger Count Range */}
                  <div className="space-y-2">
                    <Label htmlFor="passengers">Passengers</Label>
                    <div className="flex gap-2">
                      <Input
                        id="min_passengers"
                        type="number"
                        min="1"
                        max="6"
                        placeholder="Min"
                        value={filters.min_passengers}
                        onChange={(e) => setFilters({ ...filters, min_passengers: e.target.value })}
                        className="w-full"
                      />
                      <Input
                        id="max_passengers"
                        type="number"
                        min="1"
                        max="6"
                        placeholder="Max"
                        value={filters.max_passengers}
                        onChange={(e) => setFilters({ ...filters, max_passengers: e.target.value })}
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {/* Fare Range */}
                  <div className="space-y-2">
                    <Label htmlFor="fare">Fare Amount ($)</Label>
                    <div className="flex gap-2">
                      <Input
                        id="min_fare"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Min $"
                        value={filters.min_fare}
                        onChange={(e) => setFilters({ ...filters, min_fare: e.target.value })}
                        className="w-full"
                      />
                      <Input
                        id="max_fare"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Max $"
                        value={filters.max_fare}
                        onChange={(e) => setFilters({ ...filters, max_fare: e.target.value })}
                        className="w-full"
                      />
                    </div>
                  </div>

                  {/* Distance Range */}
                  <div className="space-y-2">
                    <Label htmlFor="distance">Distance (miles)</Label>
                    <div className="flex gap-2">
                      <Input
                        id="min_distance"
                        type="number"
                        step="0.1"
                        min="0"
                        placeholder="Min mi"
                        value={filters.min_distance}
                        onChange={(e) => setFilters({ ...filters, min_distance: e.target.value })}
                        className="w-full"
                      />
                      <Input
                        id="max_distance"
                        type="number"
                        step="0.1"
                        min="0"
                        placeholder="Max mi"
                        value={filters.max_distance}
                        onChange={(e) => setFilters({ ...filters, max_distance: e.target.value })}
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>

                {/* Filter Actions */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearFilters}
                    className="gap-2"
                  >
                    <X className="h-4 w-4" />
                    Clear All
                  </Button>
                  <Button
                    onClick={handleApplyFilters}
                    className="gap-2"
                  >
                    <Filter className="h-4 w-4" />
                    Apply Filters
                  </Button>
                </div>
              </div>
            </CollapsibleContent>
          </ChartCard>
        </Collapsible>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatCard
            title="Total Records"
            value={totalRecords.toLocaleString()}
            icon={Database}
            variant="primary"
          />
          <StatCard
            title="Current Page"
            value={`${page} / ${pagination?.total_pages || 1}`}
            subtitle={`Showing ${records.length} of ${totalRecords.toLocaleString()} records`}
            icon={Hash}
          />
          <StatCard
            title="Avg Fare"
            value={summary?.summary?.mean?.fare_amount ? `$${summary.summary.mean.fare_amount.toFixed(2)}` : 'N/A'}
            subtitle="Average trip fare"
            icon={Database}
          />
        </div>

        {/* Data Table */}
        {!filtersApplied && !hasActiveFilters() ? (
          <ChartCard title="No Filters Applied" subtitle="Please apply filters to load data">
            <div className="text-center py-12 text-muted-foreground">
              <Filter className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">No data loaded</p>
              <p className="text-sm mb-4">Select filters above and click "Apply Filters" to load data</p>
              <p className="text-xs">This ensures fast queries by only loading filtered data</p>
            </div>
          </ChartCard>
        ) : (
          <ChartCard 
            title="Trip Data" 
            subtitle={`Page ${page} of ${pagination?.total_pages || 1} (${totalRecords.toLocaleString()} total records)`}
          >
            {isLoading ? (
              <LoadingOverlay message="Loading data..." />
            ) : (
              <>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Vendor</TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-secondary/50"
                          onClick={() => {
                            if (orderBy === 'tpep_pickup_datetime') {
                              setOrderDirection(orderDirection === 'asc' ? 'desc' : 'asc');
                            } else {
                              setOrderBy('tpep_pickup_datetime');
                              setOrderDirection('asc');
                            }
                          }}
                        >
                          Pickup Time {orderBy === 'tpep_pickup_datetime' && (orderDirection === 'asc' ? '↑' : '↓')}
                        </TableHead>
                        <TableHead>Passengers</TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-secondary/50"
                          onClick={() => {
                            if (orderBy === 'trip_distance') {
                              setOrderDirection(orderDirection === 'asc' ? 'desc' : 'asc');
                            } else {
                              setOrderBy('trip_distance');
                              setOrderDirection('asc');
                            }
                          }}
                        >
                          Distance {orderBy === 'trip_distance' && (orderDirection === 'asc' ? '↑' : '↓')}
                        </TableHead>
                        <TableHead>Duration</TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-secondary/50"
                          onClick={() => {
                            if (orderBy === 'fare_amount') {
                              setOrderDirection(orderDirection === 'asc' ? 'desc' : 'asc');
                            } else {
                              setOrderBy('fare_amount');
                              setOrderDirection('asc');
                            }
                          }}
                        >
                          Fare {orderBy === 'fare_amount' && (orderDirection === 'asc' ? '↑' : '↓')}
                        </TableHead>
                        <TableHead>Tip</TableHead>
                        <TableHead>Total</TableHead>
                        <TableHead>Payment</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {records.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                            No data available for the selected filters
                          </TableCell>
                        </TableRow>
                      ) : (
                        records.map((record, i) => (
                          <TableRow key={i}>
                            <TableCell>
                              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-xs font-medium text-primary">
                                {record.VendorID}
                              </span>
                            </TableCell>
                            <TableCell className="text-muted-foreground text-sm">
                              {formatDate(record.tpep_pickup_datetime)}
                            </TableCell>
                            <TableCell>{record.passenger_count}</TableCell>
                            <TableCell>{record.trip_distance?.toFixed(1) || 'N/A'} mi</TableCell>
                            <TableCell>{record.trip_duration_minutes?.toFixed(0) || 'N/A'} min</TableCell>
                            <TableCell className="font-medium">{formatCurrency(record.fare_amount || 0)}</TableCell>
                            <TableCell className="text-chart-4">{formatCurrency(record.tip_amount || 0)}</TableCell>
                            <TableCell className="font-semibold text-primary">{formatCurrency(record.total_amount || 0)}</TableCell>
                            <TableCell>
                              <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                                record.payment_type === 1 
                                  ? 'bg-chart-4/20 text-chart-4' 
                                  : 'bg-chart-3/20 text-chart-3'
                              }`}>
                                {record.payment_type === 1 ? 'Card' : 'Cash'}
                              </span>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>

                {/* Pagination Controls */}
                {pagination && pagination.total_pages > 1 && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t">
                    <div className="text-sm text-muted-foreground">
                      Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalRecords)} of {totalRecords.toLocaleString()} records
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handlePageChange(1)}
                        disabled={!pagination.has_previous}
                      >
                        <ChevronsLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handlePageChange(page - 1)}
                        disabled={!pagination.has_previous}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <div className="flex items-center gap-1 px-2">
                        <span className="text-sm font-medium">Page</span>
                        <span className="text-sm">{page}</span>
                        <span className="text-sm text-muted-foreground">of</span>
                        <span className="text-sm">{pagination.total_pages}</span>
                      </div>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handlePageChange(page + 1)}
                        disabled={!pagination.has_next}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handlePageChange(pagination.total_pages)}
                        disabled={!pagination.has_next}
                      >
                        <ChevronsRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </ChartCard>
        )}

        {/* Column Descriptions */}
        <ChartCard title="Data Dictionary" subtitle="Column descriptions">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { name: 'VendorID', desc: 'Taxi vendor identifier (1 or 2)' },
              { name: 'tpep_pickup_datetime', desc: 'Trip start timestamp' },
              { name: 'tpep_dropoff_datetime', desc: 'Trip end timestamp' },
              { name: 'passenger_count', desc: 'Number of passengers' },
              { name: 'trip_distance', desc: 'Trip distance in miles' },
              { name: 'pickup_latitude', desc: 'Pickup GPS latitude' },
              { name: 'pickup_longitude', desc: 'Pickup GPS longitude' },
              { name: 'dropoff_latitude', desc: 'Dropoff GPS latitude' },
              { name: 'dropoff_longitude', desc: 'Dropoff GPS longitude' },
              { name: 'fare_amount', desc: 'Base fare in USD' },
              { name: 'tip_amount', desc: 'Tip paid in USD' },
              { name: 'total_amount', desc: 'Total amount charged' },
              { name: 'payment_type', desc: '1=Card, 2=Cash' },
              { name: 'trip_duration_minutes', desc: 'Duration in minutes' },
            ].map((col) => (
              <div key={col.name} className="rounded-lg bg-secondary/50 p-3">
                <p className="font-mono text-sm font-medium text-primary">{col.name}</p>
                <p className="text-xs text-muted-foreground">{col.desc}</p>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </DashboardLayout>
  );
}
