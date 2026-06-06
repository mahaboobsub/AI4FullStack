/**
 * LocationManager — M6 additive component.
 * Reusable card for managing multi-locations for either a patient (max 5) or a donor (backup areas).
 * Pure addition: does not modify any existing component.
 */
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Plus, Trash2, Star, Loader2, Navigation } from "lucide-react";
import { toast } from "sonner";
import {
  LocationEntry, NewLocation,
  getPatientLocations, addPatientLocation, deletePatientLocation, setPatientPrimaryLocation,
  getDonorLocations, addDonorLocation, deleteDonorLocation, setDonorPrimaryLocation,
} from "@/lib/api";

interface Props {
  entityId: string;
  kind: "patient" | "donor";
  maxLocations?: number;
}

export default function LocationManager({ entityId, kind, maxLocations }: Props) {
  const [locations, setLocations] = useState<LocationEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [geoLoading, setGeoLoading] = useState(false);
  const [form, setForm] = useState<NewLocation>({ label: "", lat: 0, lng: 0, is_primary: false, priority_order: 1 });
  const [showForm, setShowForm] = useState(false);

  const cap = maxLocations ?? (kind === "patient" ? 5 : 10);
  const api = kind === "patient"
    ? { list: getPatientLocations, add: addPatientLocation, del: deletePatientLocation, primary: setPatientPrimaryLocation }
    : { list: getDonorLocations, add: addDonorLocation, del: deleteDonorLocation, primary: setDonorPrimaryLocation };

  const load = () => {
    setLoading(true);
    api.list(entityId).then(setLocations).catch(() => setLocations([])).finally(() => setLoading(false));
  };
  useEffect(() => { if (entityId) load(); /* eslint-disable-next-line */ }, [entityId]);

  const handleAdd = async () => {
    if (!form.label.trim()) { toast.error("Enter a label (e.g. Home, Work)."); return; }
    if (form.lat < -90 || form.lat > 90 || form.lng < -180 || form.lng > 180) {
      toast.error("Invalid coordinates."); return;
    }
    if (locations.length >= cap) { toast.error(`Maximum ${cap} locations.`); return; }
    setAdding(true);
    try {
      await api.add(entityId, { ...form, priority_order: locations.length + 1 });
      toast.success("Location added.");
      setForm({ label: "", lat: 0, lng: 0, is_primary: false, priority_order: 1 });
      setShowForm(false);
      load();
    } catch (e: any) {
      toast.error(e?.message?.includes("400") ? `Maximum ${cap} locations reached.` : "Failed to add location.");
    } finally { setAdding(false); }
  };

  const handleDelete = async (locId: string) => {
    try { await api.del(entityId, locId); toast.success("Location removed."); load(); }
    catch { toast.error(kind === "patient" ? "Cannot delete the last location." : "Failed to remove."); }
  };

  const handlePrimary = async (locId: string) => {
    try { await api.primary(entityId, locId); load(); } catch { toast.error("Failed to set primary."); }
  };

  const title = kind === "patient" ? "My Search Locations" : "My Backup Areas";
  const subtitle = kind === "patient"
    ? `Up to ${cap} locations — we search outward from these.`
    : `Areas you can travel to (up to ${cap}). More areas = more chances to help.`;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 text-teal-400" /> {title}
        </h3>
        <span className="text-[10px] text-slate-500">{locations.length}/{cap}</span>
      </div>
      <p className="text-xs text-slate-400 mb-4">{subtitle}</p>

      {loading ? (
        <div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-slate-500" /></div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence>
            {locations.map((loc) => (
              <motion.div
                key={loc.location_id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                className="flex items-center justify-between bg-slate-800/60 border border-slate-700 rounded-xl px-3 py-2"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <button
                    onClick={() => handlePrimary(loc.location_id)}
                    title={loc.is_primary ? "Primary location" : "Set as primary"}
                    className={loc.is_primary ? "text-amber-400" : "text-slate-600 hover:text-amber-400"}
                  >
                    <Star className="w-4 h-4" fill={loc.is_primary ? "currentColor" : "none"} />
                  </button>
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-white truncate">{loc.label}</div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)} · {loc.geohash}
                    </div>
                  </div>
                </div>
                <button onClick={() => handleDelete(loc.location_id)} className="text-slate-600 hover:text-red-400">
                  <Trash2 className="w-4 h-4" />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>

          {locations.length === 0 && (
            <p className="text-xs text-slate-500 italic text-center py-3">No locations yet. Add one below.</p>
          )}
        </div>
      )}

      {/* Add form */}
      {locations.length < cap && (
        <div className="mt-3">
          {!showForm ? (
            <button
              onClick={() => setShowForm(true)}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-bold
                         bg-teal-500/15 text-teal-300 border border-teal-500/30 hover:bg-teal-500/25 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> Add Location
            </button>
          ) : (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
              className="space-y-2 bg-slate-800/40 border border-slate-700 rounded-xl p-3">
              <input
                className="w-full bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5"
                placeholder="Label (Home, Work, Hostel...)"
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
              />
              <div className="grid grid-cols-2 gap-2">
                <input type="number" step="any"
                  className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5"
                  placeholder="Latitude" value={form.lat || ""}
                  onChange={(e) => setForm({ ...form, lat: parseFloat(e.target.value) || 0 })} />
                <input type="number" step="any"
                  className="bg-slate-900 border border-slate-700 text-white text-xs rounded px-2 py-1.5"
                  placeholder="Longitude" value={form.lng || ""}
                  onChange={(e) => setForm({ ...form, lng: parseFloat(e.target.value) || 0 })} />
              </div>
              {/* Use My Location button */}
              <button
                type="button"
                disabled={geoLoading}
                onClick={() => {
                  if (!navigator.geolocation) {
                    toast.error("Geolocation not supported by your browser.");
                    return;
                  }
                  setGeoLoading(true);
                  navigator.geolocation.getCurrentPosition(
                    (pos) => {
                      setForm({ ...form, lat: pos.coords.latitude, lng: pos.coords.longitude, label: form.label || "My Location" });
                      setGeoLoading(false);
                      toast.success("Location detected from GPS.");
                    },
                    (err) => {
                      setGeoLoading(false);
                      toast.error(err.message || "Failed to get location. Please enter manually.");
                    },
                    { enableHighAccuracy: true, timeout: 10000 }
                  );
                }}
                className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold
                           bg-blue-500/15 text-blue-300 border border-blue-500/30 hover:bg-blue-500/25 transition-colors"
              >
                {geoLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Navigation className="w-3.5 h-3.5" />}
                {geoLoading ? "Detecting..." : "Use My Location"}
              </button>
              <label className="flex items-center gap-2 text-[11px] text-slate-400">
                <input type="checkbox" checked={form.is_primary}
                  onChange={(e) => setForm({ ...form, is_primary: e.target.checked })} />
                Set as primary location
              </label>
              <div className="flex gap-2">
                <button onClick={handleAdd} disabled={adding}
                  className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold
                             bg-teal-500/20 text-teal-300 border border-teal-500/30 hover:bg-teal-500/30">
                  {adding ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Save"}
                </button>
                <button onClick={() => setShowForm(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-400 border border-slate-700 hover:bg-slate-800">
                  Cancel
                </button>
              </div>
              <p className="text-[10px] text-slate-600">
                Tip: get coordinates from Google Maps (right-click → copy lat,lng).
              </p>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}
