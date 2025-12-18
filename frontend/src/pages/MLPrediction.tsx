import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout';
import { ChartCard } from '@/components/common';
import { HorizontalBarChart } from '@/components/charts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Brain, MapPin, Clock, Users, DollarSign, Loader2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { getModelMetrics, predictFare, type ModelMetrics } from '@/api';

const MODEL_OPTIONS = [
  { value: 'random_forest', label: 'Random Forest' },
  { value: 'gbt', label: 'Gradient Boosted Trees' },
  { value: 'linear_regression', label: 'Linear Regression' },
];

export default function MLPrediction() {
  const [selectedModel, setSelectedModel] = useState<string>('random_forest');
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    pickupTime: '',
    pickupLat: '40.7589',
    pickupLng: '-73.9851',
    dropoffLat: '40.6413',
    dropoffLng: '-73.7781',
    passengers: '2',
    distance: '',
  });

  const { data: modelMetrics, isLoading: metricsLoading } = useQuery<ModelMetrics>({
    queryKey: ['model-metrics', selectedModel],
    queryFn: () => getModelMetrics(selectedModel),
    staleTime: 5 * 60 * 1000,
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handlePredict = async () => {
    setIsLoading(true);
    
    try {
      const distance = parseFloat(formData.distance) || 
        calculateDistance(
          parseFloat(formData.pickupLat),
          parseFloat(formData.pickupLng),
          parseFloat(formData.dropoffLat),
          parseFloat(formData.dropoffLng)
        );
      
      // Use user-provided pickup *time* (HH:MM) with today's date, otherwise "now"
      const now = new Date();
      const pad = (n: number) => n.toString().padStart(2, '0');
      let pickupDatetime: string;

      if (formData.pickupTime) {
        const [hStr, mStr] = formData.pickupTime.split(':');
        const h = parseInt(hStr ?? '', 10);
        const m = parseInt(mStr ?? '0', 10);

        if (!Number.isNaN(h) && h >= 0 && h < 24 && !Number.isNaN(m) && m >= 0 && m < 60) {
          pickupDatetime = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(
            now.getDate()
          )} ${pad(h)}:${pad(m)}:00`;
        } else {
          pickupDatetime = now.toISOString().slice(0, 19).replace('T', ' ');
        }
      } else {
        pickupDatetime = now.toISOString().slice(0, 19).replace('T', ' ');
      }
      
      const result = await predictFare({
        pickup_datetime: pickupDatetime,
        pickup_latitude: parseFloat(formData.pickupLat),
        pickup_longitude: parseFloat(formData.pickupLng),
        dropoff_latitude: parseFloat(formData.dropoffLat),
        dropoff_longitude: parseFloat(formData.dropoffLng),
        passenger_count: parseInt(formData.passengers) || 1,
        trip_distance: distance
      });
      
      if (result.error) {
        toast({
          title: "Prediction Error",
          description: result.message || result.error,
          variant: "destructive"
        });
        setPrediction(null);
      } else {
        setPrediction(result.predicted_fare);
        toast({
          title: "Prediction Complete",
          description: `Predicted fare: $${result.predicted_fare.toFixed(2)}`,
        });
      }
    } catch (error: any) {
      toast({
        title: "Prediction Error",
        description: error.message || "Failed to get prediction from ML model",
        variant: "destructive"
      });
      setPrediction(null);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number) => {
    const R = 3959;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            ML Fare Prediction
          </h1>
          <p className="text-muted-foreground">
            Predict taxi fares using machine learning
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <ChartCard title="Fare Predictor" subtitle="Enter trip details">
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <Clock className="h-4 w-4 text-chart-4" />
                  Pickup Time
                </div>
                <Input
                  id="pickupTime"
                  name="pickupTime"
                  type="time"
                  value={formData.pickupTime}
                  onChange={handleInputChange}
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <MapPin className="h-4 w-4 text-primary" />
                  Pickup Location
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="pickupLat">Latitude</Label>
                    <Input
                      id="pickupLat"
                      name="pickupLat"
                      type="number"
                      step="0.0001"
                      value={formData.pickupLat}
                      onChange={handleInputChange}
                      placeholder="40.7589"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pickupLng">Longitude</Label>
                    <Input
                      id="pickupLng"
                      name="pickupLng"
                      type="number"
                      step="0.0001"
                      value={formData.pickupLng}
                      onChange={handleInputChange}
                      placeholder="-73.9851"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <MapPin className="h-4 w-4 text-chart-2" />
                  Dropoff Location
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="dropoffLat">Latitude</Label>
                    <Input
                      id="dropoffLat"
                      name="dropoffLat"
                      type="number"
                      step="0.0001"
                      value={formData.dropoffLat}
                      onChange={handleInputChange}
                      placeholder="40.6413"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="dropoffLng">Longitude</Label>
                    <Input
                      id="dropoffLng"
                      name="dropoffLng"
                      type="number"
                      step="0.0001"
                      value={formData.dropoffLng}
                      onChange={handleInputChange}
                      placeholder="-73.7781"
                    />
                  </div>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-chart-3" />
                    <Label htmlFor="passengers">Passengers</Label>
                  </div>
                  <Input
                    id="passengers"
                    name="passengers"
                    type="number"
                    min="1"
                    max="6"
                    value={formData.passengers}
                    onChange={handleInputChange}
                    placeholder="2"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-chart-4" />
                    <Label htmlFor="distance">Distance (mi, optional)</Label>
                  </div>
                  <Input
                    id="distance"
                    name="distance"
                    type="number"
                    step="0.1"
                    value={formData.distance}
                    onChange={handleInputChange}
                    placeholder="Auto-calculate"
                  />
                </div>
              </div>

              <Button 
                onClick={handlePredict} 
                className="w-full gap-2"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Predicting...
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4" />
                    Predict Fare
                  </>
                )}
              </Button>

              {prediction !== null && (
                <div className="rounded-lg border border-primary/30 bg-primary/10 p-6 text-center glow-primary">
                  <p className="text-sm text-muted-foreground mb-2">Predicted Fare</p>
                  <p className="text-4xl font-bold text-primary">
                    ${prediction.toFixed(2)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Based on {MODEL_OPTIONS.find(m => m.value === selectedModel)?.label || 'selected'} model
                  </p>
                </div>
              )}
            </div>
          </ChartCard>

          <ChartCard title="Feature Importance" subtitle="What influences the prediction">
            {metricsLoading ? (
              <div className="flex items-center justify-center h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : modelMetrics?.feature_importance && Object.keys(modelMetrics.feature_importance).length > 0 ? (
              <HorizontalBarChart 
                data={Object.entries(modelMetrics.feature_importance)
                  .map(([feature, importance]) => ({
                    feature: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    importance: typeof importance === 'number' ? importance : 0
                  }))
                  .sort((a, b) => b.importance - a.importance)
                  .slice(0, 10)}
                nameKey="feature"
                valueKey="importance"
                height={400}
                colors={['hsl(187, 85%, 53%)', 'hsl(187, 85%, 48%)', 'hsl(187, 85%, 43%)']}
              />
            ) : (
              <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                <p>Feature importance data not available</p>
              </div>
            )}
          </ChartCard>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground mb-2">Model Type</p>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                {MODEL_OPTIONS.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    {model.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">R² Score</p>
            <p className="text-xl font-bold text-chart-4">
              {metricsLoading ? '...' : (modelMetrics?.r2?.toFixed(2) || 'N/A')}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">RMSE</p>
            <p className="text-xl font-bold text-chart-3">
              {metricsLoading ? '...' : (modelMetrics?.rmse ? modelMetrics.rmse.toFixed(2) : 'N/A')}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm text-muted-foreground">Training Samples</p>
            <p className="text-xl font-bold text-primary">
              {metricsLoading ? '...' : (modelMetrics?.training_samples_display || 'N/A')}
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
