import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in React/TypeScript
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

// Fix default icon paths
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: icon,
  shadowUrl: iconShadow,
});

interface Hotspot {
  latitude: number;
  longitude: number;
  trip_count: number;
}

interface TaxiMapProps {
  pickupHotspots?: Hotspot[];
  dropoffHotspots?: Hotspot[];
  showPickups?: boolean;
  showDropoffs?: boolean;
  height?: string;
}

function MapBounds({ pickupHotspots, dropoffHotspots }: { pickupHotspots?: Hotspot[]; dropoffHotspots?: Hotspot[] }) {
  const map = useMap();
  
  useEffect(() => {
    if (!map || !L) return;
    
    const allPoints: [number, number][] = [];
    
    if (pickupHotspots) {
      pickupHotspots.forEach(h => allPoints.push([h.latitude, h.longitude]));
    }
    if (dropoffHotspots) {
      dropoffHotspots.forEach(h => allPoints.push([h.latitude, h.longitude]));
    }
    
    if (allPoints.length > 0) {
      const bounds = L.latLngBounds(allPoints);
      map.fitBounds(bounds, { padding: [50, 50] });
    } else {
      // Default to NYC if no data
      map.setView([40.7128, -74.0060], 11);
    }
  }, [map, pickupHotspots, dropoffHotspots]);
  
  return null;
}

export function TaxiMap({ 
  pickupHotspots = [], 
  dropoffHotspots = [], 
  showPickups = true,
  showDropoffs = true,
  height = '400px'
}: TaxiMapProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Calculate max trip count for scaling marker sizes
  const maxTrips = Math.max(
    ...pickupHotspots.map(h => h.trip_count),
    ...dropoffHotspots.map(h => h.trip_count),
    1
  );

  // Don't render map on server side
  if (!isMounted) {
    return (
      <div className="w-full rounded-lg overflow-hidden flex items-center justify-center bg-secondary/30" style={{ height }}>
        <p className="text-muted-foreground">Loading map...</p>
      </div>
    );
  }

  return (
    <div className="w-full rounded-lg overflow-hidden" style={{ height }}>
      <MapContainer
        center={[40.7128, -74.0060]}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapBounds pickupHotspots={pickupHotspots} dropoffHotspots={dropoffHotspots} />
        
        {showPickups && pickupHotspots.map((hotspot, idx) => {
          const radius = Math.max(5, (hotspot.trip_count / maxTrips) * 15);
          return (
            <CircleMarker
              key={`pickup-${idx}`}
              center={[hotspot.latitude, hotspot.longitude]}
              radius={radius}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.6,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-sm">
                  <strong>Pickup Hotspot</strong>
                  <br />
                  Trips: {hotspot.trip_count.toLocaleString()}
                  <br />
                  Location: {hotspot.latitude.toFixed(4)}, {hotspot.longitude.toFixed(4)}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
        
        {showDropoffs && dropoffHotspots.map((hotspot, idx) => {
          const radius = Math.max(5, (hotspot.trip_count / maxTrips) * 15);
          return (
            <CircleMarker
              key={`dropoff-${idx}`}
              center={[hotspot.latitude, hotspot.longitude]}
              radius={radius}
              pathOptions={{
                color: '#10b981',
                fillColor: '#10b981',
                fillOpacity: 0.6,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-sm">
                  <strong>Dropoff Hotspot</strong>
                  <br />
                  Trips: {hotspot.trip_count.toLocaleString()}
                  <br />
                  Location: {hotspot.latitude.toFixed(4)}, {hotspot.longitude.toFixed(4)}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
