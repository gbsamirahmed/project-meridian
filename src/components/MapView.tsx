import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

import {
  removeTemperatureLayer,
  updateTemperatureLayer,
} from "../services/temperatureLayer";

import {
  removeCloudLayer,
  updateCloudLayer,
} from "../services/cloudLayer";

import {
  removePrecipitationLayer,
  updatePrecipitationLayer,
} from "../services/precipitationLayer";

import {
  removePressureLayer,
  updatePressureLayer,
} from "../services/pressureLayer";

import {
  removeWindLayer,
  updateWindLayer,
} from "../services/windLayer";

import type { SelectedLocation } from "../types/location";
import type { WeatherLayer } from "../types/layer";
import type { GridPoint } from "../types/gridPoint";

import "maplibre-gl/dist/maplibre-gl.css";

interface MapViewProps {
  selectedLocation: SelectedLocation | null;
  selectedLayer: WeatherLayer;
  gridPoints: GridPoint[];
  forecastHour: number;
  onLocationSelect: (location: SelectedLocation) => void;
}

export default function MapView({
  selectedLocation,
  selectedLayer,
  gridPoints,
  forecastHour,
  onLocationSelect,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [-0.1276, 51.5072],
      zoom: 9,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("click", (event) => {
      onLocationSelect({
        latitude: event.lngLat.lat,
        longitude: event.lngLat.lng,
      });
    });

    mapRef.current = map;

    return () => {
      removeTemperatureLayer(map);
      removeCloudLayer(map);
      removePrecipitationLayer(map);
      removePressureLayer(map);
      removeWindLayer(map);

      map.remove();
      mapRef.current = null;
    };
  }, [onLocationSelect]);

  useEffect(() => {
    if (!selectedLocation || !mapRef.current) return;

    const lngLat: [number, number] = [
      selectedLocation.longitude,
      selectedLocation.latitude,
    ];

    if (selectedLayer !== "none" && gridPoints.length > 0) {
      const longitudes = gridPoints.map((point) => point.longitude);
      const latitudes = gridPoints.map((point) => point.latitude);

      const bounds = new maplibregl.LngLatBounds(
        [Math.min(...longitudes), Math.min(...latitudes)],
        [Math.max(...longitudes), Math.max(...latitudes)]
      );

      mapRef.current.fitBounds(bounds, {
        padding: 100,
        duration: 1000,
      });
    } else {
      mapRef.current.flyTo({
        center: lngLat,
        zoom: 10,
        essential: true,
      });
    }

    if (markerRef.current) {
      markerRef.current.setLngLat(lngLat);
    } else {
      markerRef.current = new maplibregl.Marker()
        .setLngLat(lngLat)
        .addTo(mapRef.current);
    }
  }, [selectedLocation, selectedLayer, gridPoints]);

  useEffect(() => {
    if (!mapRef.current) return;

    removeTemperatureLayer(mapRef.current);
    removeCloudLayer(mapRef.current);
    removePrecipitationLayer(mapRef.current);
    removePressureLayer(mapRef.current);
    removeWindLayer(mapRef.current);

    if (gridPoints.length === 0) return;

    if (selectedLayer === "temperature") {
      updateTemperatureLayer(
        mapRef.current,
        gridPoints,
        forecastHour
      );
    }

    if (selectedLayer === "clouds") {
      updateCloudLayer(
        mapRef.current,
        gridPoints,
        forecastHour
      );
    }

    if (selectedLayer === "precipitation") {
      updatePrecipitationLayer(
        mapRef.current,
        gridPoints,
        forecastHour
      );
    }

    if (selectedLayer === "pressure") {
      updatePressureLayer(
        mapRef.current,
        gridPoints,
        forecastHour
      );
    }

    if (selectedLayer === "wind") {
      updateWindLayer(
        mapRef.current,
        gridPoints,
        forecastHour
      );
    }
  }, [gridPoints, selectedLayer, forecastHour]);

  return (
    <div className="map-container-wrapper">
      <div className="map-container" ref={mapContainer} />

      <div className="layer-badge">
        Layer: {selectedLayer}
      </div>
    </div>
  );
}