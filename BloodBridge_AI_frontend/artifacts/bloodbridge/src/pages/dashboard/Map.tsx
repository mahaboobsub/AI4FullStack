import { useState, useEffect, lazy, Suspense } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { getBloodStock, refreshBloodBanks, type BloodBank } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Phone, Navigation, Droplet, Car, AlertTriangle, RefreshCcw } from "lucide-react";
import { toast } from "sonner";
import 'leaflet/dist/leaflet.css';

const MapContainer = lazy(() => import("react-leaflet").then(mod => ({ default: mod.MapContainer })));
const TileLayer = lazy(() => import("react-leaflet").then(mod => ({ default: mod.TileLayer })));
const Marker = lazy(() => import("react-leaflet").then(mod => ({ default: mod.Marker })));
const Popup = lazy(() => import("react-leaflet").then(mod => ({ default: mod.Popup })));

export default function MapView() {
  const [banks, setBanks] = useState<BloodBank[]>([]);
  const [bloodType, setBloodType] = useState<string>("B+");
  const [isClient, setIsClient] = useState(false);
  const [selectedBankId, setSelectedBankId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    setIsClient(true);
    getBloodStock("Hyderabad").then(setBanks);
  }, []);

  const handleRefreshInventory = async () => {
    setRefreshing(true);
    try {
      await refreshBloodBanks();
      const updated = await getBloodStock("Hyderabad");
      setBanks(updated);
      toast.success("Inventory refreshed from e-RaktKosh");
    } catch {
      toast.error("Failed to refresh inventory");
    } finally {
      setRefreshing(false);
    }
  };

  const bloodTypes = ["A+","A-","B+","B-","AB+","AB-","O+","O-"];
  const sortedBanks = [...banks].sort((a,b) => (b.units[bloodType] || 0) - (a.units[bloodType] || 0));
  
  // Check for critical shortage
  const hasZeroUnits = sortedBanks.some(b => (b.units[bloodType] || 0) === 0);
  const zeroUnitCount = sortedBanks.filter(b => (b.units[bloodType] || 0) === 0).length;

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-52px)] w-full overflow-hidden">
        {/* Left: Map */}
        <div className="flex-1 relative bg-slate-100 z-0">
          <div className="absolute bottom-6 left-6 z-[400]">
            <div className="bg-white/90 backdrop-blur px-3 py-1.5 rounded-full shadow-lg border border-slate-200 text-[10px] font-mono font-bold flex items-center gap-2 text-slate-600">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Connected to e-RaktKosh · Last updated 2 min ago
            </div>
          </div>
          
          {isClient && (
            <Suspense fallback={<div className="w-full h-full flex items-center justify-center">Loading Map...</div>}>
              <MapContainer 
                center={[17.42, 78.46]} 
                zoom={12} 
                style={{ height: '100%', width: '100%' }}
                zoomControl={false}
              >
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                {banks.map(bank => {
                  const units = bank.units[bloodType] || 0;
                  const color = units > 5 ? "emerald" : units > 0 ? "amber" : "red";
                  
                  return (
                    <Marker key={bank.id} position={[bank.lat, bank.lng]} eventHandlers={{ click: () => setSelectedBankId(bank.id) }}>
                      <Popup>
                        <div className="p-1 min-w-[150px]">
                          <h3 className="font-bold text-sm mb-2">{bank.name}</h3>
                          <Badge className={`bg-${color}-100 text-${color}-700 border-${color}-200`}>
                            {units} units of {bloodType}
                          </Badge>
                        </div>
                      </Popup>
                    </Marker>
                  )
                })}
                <Marker position={[17.4480, 78.4982]}>
                  <Popup><strong>KIMS Secunderabad</strong><br/>Emergency OC Location</Popup>
                </Marker>
              </MapContainer>
            </Suspense>
          )}
        </div>

        {/* Right: List Panel */}
        <div className="w-[420px] border-l border-border bg-slate-50 flex flex-col z-10 shadow-[-4px_0_15px_rgba(0,0,0,0.05)]">
          {/* Summary Strip */}
          <div className="bg-slate-800 text-white px-4 py-2 text-[10px] font-mono flex items-center justify-between">
            <span>8 Blood Banks</span>
            <span>3 KIMS Adjacent</span>
            <span className="text-teal-400">{bloodType} available at {sortedBanks.filter(b=>(b.units[bloodType]||0)>0).length} locations</span>
          </div>

          <div className="p-4 bg-white border-b border-border shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold flex items-center gap-2">
                <Droplet className="w-4 h-4 text-red-500" /> 
                Live Inventory Network
              </h2>
              <Button
                size="sm"
                variant="outline"
                className="text-xs gap-1.5 h-8"
                disabled={refreshing}
                onClick={handleRefreshInventory}
              >
                <RefreshCcw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
            </div>
            
            {/* Horizontal Pill Filters */}
            <div className="flex flex-wrap gap-1.5 mb-2">
              {bloodTypes.map(bt => (
                <button
                  key={bt}
                  onClick={() => setBloodType(bt)}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                    bloodType === bt 
                      ? "bg-[#C8102E] text-white shadow-md scale-105" 
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {bt}
                </button>
              ))}
            </div>
          </div>
          
          {hasZeroUnits && (
            <div className="bg-amber-50 border-y border-amber-200 px-4 py-3 flex gap-3 items-start">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-bold text-amber-900">⚠ No {bloodType} units available at {zeroUnitCount} locations</p>
                <p className="text-[10px] text-amber-700 mt-1">AI predictive routing engaged to secure remaining supply.</p>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
            {sortedBanks.map(bank => {
              const targetUnits = bank.units[bloodType] || 0;
              const isSelected = selectedBankId === bank.id;
              
              return (
                <Card 
                  key={bank.id} 
                  className={`cursor-pointer transition-all border ${isSelected ? 'ring-2 ring-teal-500 border-transparent shadow-md' : 'hover:border-slate-300'}`}
                  onClick={() => setSelectedBankId(bank.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="font-bold text-sm leading-tight pr-2">{bank.name}</h3>
                      <div className={`px-2 py-1 rounded text-xs font-bold font-mono whitespace-nowrap ${targetUnits > 5 ? 'bg-emerald-100 text-emerald-700' : targetUnits > 0 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>
                        {targetUnits} units
                      </div>
                    </div>
                    
                    {/* Blood Type Grid (2x4) */}
                    <div className="grid grid-cols-4 gap-1 mb-4">
                      {bloodTypes.map(bt => {
                        const count = bank.units[bt] || 0;
                        const c = count > 5 ? "emerald" : count > 0 ? "amber" : "red";
                        const bgColors:any = { emerald: "bg-emerald-50 text-emerald-700", amber: "bg-amber-50 text-amber-700", red: "bg-red-50 text-red-500 opacity-50" };
                        
                        return (
                          <div key={bt} className={`text-[9px] font-mono font-bold text-center rounded border border-slate-100 py-0.5 ${bgColors[c]} ${bloodType === bt ? 'ring-1 ring-slate-400' : ''}`}>
                            {bt}: {count}
                          </div>
                        );
                      })}
                    </div>

                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-md">
                        <Car className="w-3.5 h-3.5" />
                        <span className="font-medium">{bank.distance_km} km · {bank.drive_min} min</span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="flex-1 h-9 text-xs border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700">
                        <Phone className="w-3.5 h-3.5 mr-1.5"/> Emergency Call
                      </Button>
                      <Button size="sm" className="flex-1 h-9 text-xs bg-blue-600 hover:bg-blue-700 text-white">
                        <Navigation className="w-3.5 h-3.5 mr-1.5"/> Route
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}