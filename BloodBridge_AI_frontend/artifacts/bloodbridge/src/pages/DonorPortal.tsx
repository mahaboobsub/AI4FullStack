import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";

import { HeartPulse, Medal, Flame, AlertCircle, Shield, Zap, Lock, Heart, LogOut, Calendar, Pause, Play, ShieldCheck, Download, Trash2, Trophy, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SiTelegram } from "react-icons/si";
import CountUp from "react-countup";
import { motion } from "framer-motion";
import { getDonor, getDonorImpactStories, setDonorAvailability, getDonorRank, getDonorActiveRequest, getDonorEligibility, getConsentSummary, revokeConsent, exportDonorData, eraseDonorData, getLeaderboard, updateDonorProfile, type Donor, type DonorRank, type ActiveRequest, type EligibilityResult, type ConsentSummary, type LeaderboardEntry } from "@/lib/api";
import LocationManager from "@/components/LocationManager";
import HealthStatusControl from "@/components/HealthStatusControl";
import BloodBridgeCard from "@/components/BloodBridgeCard";

const BADGE_CONFIG: Record<string, { icon: React.ElementType; color: string; gradient: string; label: string; description: string }> = {
  blood_hero: { icon: Medal, color: "amber", gradient: "from-amber-500/20 to-amber-900/10", label: "Blood Hero", description: "10+ Donations" },
  life_saver: { icon: HeartPulse, color: "teal", gradient: "from-teal-500/20 to-teal-900/10", label: "Life Saver", description: "Matched 3x" },
  crisis_hero: { icon: Zap, color: "red", gradient: "from-red-500/20 to-red-900/10", label: "Crisis Hero", description: "Respond < 15m" },
  rare_guardian: { icon: Shield, color: "purple", gradient: "from-purple-500/20 to-purple-900/10", label: "Rare Guardian", description: "Negative group" },
  weekend_warrior: { icon: Flame, color: "orange", gradient: "from-orange-500/20 to-orange-900/10", label: "Weekend Warrior", description: "5 weekend donations" },
};

const ALL_BADGES = ["blood_hero", "life_saver", "crisis_hero", "rare_guardian", "weekend_warrior"];

export default function DonorPortal() {
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [donor, setDonor] = useState<Donor | null>(null);
  const [rank, setRank] = useState<DonorRank | null>(null);
  const [activeRequest, setActiveRequest] = useState<ActiveRequest | null>(null);
  const [impactStories, setImpactStories] = useState<string[]>([]);
  const [isAvailable, setIsAvailable] = useState(true);
  const [toggleLoading, setToggleLoading] = useState(false);
  const [eligibility, setEligibility] = useState<EligibilityResult | null>(null);
  const [consent, setConsent] = useState<ConsentSummary | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [privacyLoading, setPrivacyLoading] = useState<string | null>(null);
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [profileForm, setProfileForm] = useState({ name: "", phone: "", city: "", preferred_language: "Hindi" });
  const [profileSaving, setProfileSaving] = useState(false);

  useEffect(() => {
    setMounted(true);
    const donorId = localStorage.getItem("donor_id") || "D-THREE-001";

    // Fetch donor profile (GAP-05: Single Fetch)
    getDonor(donorId)
      .then(d => {
        setDonor(d);
        setLoading(false);
        setIsAvailable(d?.is_active !== false); // GAP-07
        // Fetch leaderboard for donor's city
        if (d?.city) {
          getLeaderboard(d.city).then(lb => setLeaderboard(lb.slice(0, 10))).catch(() => setLeaderboard([]));
        }
      })
      .catch(() => {
        // If donor not found, try fallback
        if (donorId !== "D-THREE-001") {
          getDonor("D-THREE-001")
            .then(d => { setDonor(d); setLoading(false); })
            .catch(() => { setDonor(null); setLoading(false); });
        } else {
          setDonor(null);
          setLoading(false);
        }
      });

    // Fetch impact stories (GAP-06)
    getDonorImpactStories(donorId)
      .then(setImpactStories)
      .catch(() => setImpactStories([]));

    // Fetch rank
    getDonorRank(donorId)
      .then(setRank)
      .catch(() => setRank(null));

    // Fetch active emergency request
    getDonorActiveRequest(donorId)
      .then(setActiveRequest)
      .catch(() => setActiveRequest(null));

    // Fetch eligibility
    getDonorEligibility(donorId)
      .then(setEligibility)
      .catch(() => setEligibility(null));

    // Fetch consent summary (DPDP)
    getConsentSummary(donorId)
      .then(setConsent)
      .catch(() => setConsent(null));
  }, []);

  const firstName = donor?.name?.split(" ")[0] ?? "Hero";
  const livesCount = donor?.lives_saved ?? 0;
  const donationCount = donor?.donation_count ?? 0;
  const responseRate = Math.round((donor?.response_rate ?? 0) * 100);
  const bloodType = donor?.blood_type ?? "O+";
  const badges = donor?.badges ?? [];
  const cityRank = rank?.rank ?? 0;
  const hasTelegram = !!donor?.telegram_chat_id;

  // Show spinner only while initial load
  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-[#030712] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-[#030712] text-slate-800 dark:text-slate-200 font-sans pb-20 relative selection:bg-red-500/30">
      <div className="absolute top-4 left-4 z-50">
        <button
          onClick={() => window.history.back()}
          className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors bg-white/80 dark:bg-slate-100 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-700 px-3 py-1.5 rounded-full backdrop-blur-sm"
        >
          ← Back
        </button>
      </div>
      <div className="absolute top-4 right-4 z-50"><ThemeToggle /></div>
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(248,250,252,1),rgba(255,255,255,1))] dark:bg-[radial-gradient(ellipse_at_top_right,rgba(20,10,20,1),rgba(3,7,18,1))] z-[-1]" />
      
      <div className="max-w-md mx-auto px-4 pt-10 relative z-10 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-2">
          <div>
            <h1 className="text-3xl font-serif font-bold text-slate-900 dark:text-white mb-2">Namaste, {firstName}</h1>
            <div className="flex items-center gap-2">
              {cityRank > 0 && (
                <span className="px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40 text-[10px] font-black uppercase tracking-widest shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                  Rank #{cityRank} {rank?.city || "City"}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => {
                localStorage.removeItem("donor_id");
                localStorage.removeItem("auth_token");
                window.location.href = "/";
              }}
              className="text-slate-400 hover:text-white transition-colors"
              title="Log out"
            >
              <LogOut className="w-5 h-5" />
            </button>
            <div className="relative">
              <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 overflow-hidden ring-2 ring-teal-500 ring-offset-2 ring-offset-[#030712]">
                <img src={`https://api.dicebear.com/7.x/notionists/svg?seed=${firstName}`} alt="Avatar" className="w-full h-full object-cover" />
              </div>
              <div className="absolute -bottom-2 -right-1 w-6 h-6 bg-red-600 rounded-full border-2 border-[#030712] flex items-center justify-center text-[10px] font-mono font-bold text-white shadow-sm">
                {bloodType}
              </div>
            </div>
          </div>
        </div>

        {/* Edit Profile */}
        <div className="relative">
          <button
            onClick={() => {
              setProfileForm({
                name: donor?.name || "",
                phone: "",
                city: donor?.city || "",
                preferred_language: donor?.preferred_language || "Hindi",
              });
              setShowProfileEdit(!showProfileEdit);
            }}
            className="absolute -top-14 right-0 p-2 rounded-full bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-white transition-colors"
            title="Edit Profile"
          >
            <Pencil className="w-4 h-4" />
          </button>

          {showProfileEdit && (
            <div className="bg-slate-100 dark:bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
              <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider">Edit Profile</h3>
              <div className="space-y-2">
                <input
                  className="w-full bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-3 py-2"
                  placeholder="Name"
                  value={profileForm.name}
                  onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                />
                <input
                  className="w-full bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-3 py-2"
                  placeholder="Phone"
                  value={profileForm.phone}
                  onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                />
                <input
                  className="w-full bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-3 py-2"
                  placeholder="City"
                  value={profileForm.city}
                  onChange={(e) => setProfileForm({ ...profileForm, city: e.target.value })}
                />
                <div className="flex items-center gap-2">
                  <input
                    className="flex-1 bg-slate-800/50 border border-slate-700 text-slate-400 text-xs rounded-lg px-3 py-2 cursor-not-allowed"
                    value={bloodType}
                    disabled
                    title="Blood type is set via OCR and cannot be changed"
                  />
                  <span className="text-[9px] text-slate-500">OCR (readonly)</span>
                </div>
                <select
                  className="w-full bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-3 py-2"
                  value={profileForm.preferred_language}
                  onChange={(e) => setProfileForm({ ...profileForm, preferred_language: e.target.value })}
                >
                  <option value="Hindi">Hindi</option>
                  <option value="English">English</option>
                  <option value="Telugu">Telugu</option>
                </select>
                <div className="flex gap-2 pt-1">
                  <Button
                    size="sm"
                    disabled={profileSaving}
                    onClick={async () => {
                      if (!donor) return;
                      setProfileSaving(true);
                      try {
                        const data: Record<string, string> = {};
                        if (profileForm.name.trim()) data.name = profileForm.name.trim();
                        if (profileForm.phone.trim()) data.phone = profileForm.phone.trim();
                        if (profileForm.city.trim()) data.city = profileForm.city.trim();
                        data.preferred_language = profileForm.preferred_language;
                        await updateDonorProfile(donor.donor_id, data);
                        // Refresh donor
                        const updated = await getDonor(donor.donor_id);
                        setDonor(updated);
                        setShowProfileEdit(false);
                      } catch {} finally { setProfileSaving(false); }
                    }}
                    className="flex-1 bg-teal-600 hover:bg-teal-700 text-white text-xs"
                  >
                    {profileSaving ? "Saving..." : "Save"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowProfileEdit(false)}
                    className="text-xs border-slate-700 text-slate-400"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Impact Card */}
        <div className="bg-gradient-to-br from-red-900/40 to-red-950/20 border border-red-800/30 rounded-3xl p-6 relative overflow-hidden shadow-xl shadow-red-900/10">
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 blur-3xl rounded-full" />
          
          <div className="flex items-center gap-2 text-red-400 font-bold text-xs tracking-widest uppercase mb-4">
            <HeartPulse className="w-4 h-4" /> Lifetime Impact
          </div>
          
          <div className="flex flex-col mb-8">
            <div className="text-7xl font-black font-mono text-white tracking-tighter leading-none">
              {mounted ? <CountUp end={livesCount} duration={2} /> : "0"}
            </div>
            <div className="text-red-300/80 text-sm font-medium mt-1 uppercase tracking-widest">lives saved</div>
          </div>
          
          <div className="grid grid-cols-4 gap-2 pt-4 border-t border-red-900/30">
            <div>
              <div className="text-lg font-bold text-white">{donationCount}</div>
              <div className="text-[9px] text-red-300/60 uppercase font-bold">Donations</div>
            </div>
            <div>
              <div className="text-lg font-bold text-white">{responseRate}%</div>
              <div className="text-[9px] text-red-300/60 uppercase font-bold">Response</div>
            </div>
            <div>
              <div className="text-lg font-bold text-white">{donor?.last_donation_days != null ? `${Math.floor(donor.last_donation_days / 30)}m` : "—"}</div>
              <div className="text-[9px] text-red-300/60 uppercase font-bold">Last</div>
            </div>
            <div>
              <div className="text-lg font-bold text-white">{badges.length}</div>
              <div className="text-[9px] text-red-300/60 uppercase font-bold">Badges</div>
            </div>
          </div>
        </div>

        {/* Patient Emergency Card — Real data from active-request API */}
        {activeRequest ? (
          <div className="bg-red-950/30 border border-red-800/30 rounded-3xl p-5 relative overflow-hidden">
            <div className="absolute right-4 top-4 w-12 h-12 rounded-full overflow-hidden border border-red-900/50">
              <img src={`https://api.dicebear.com/7.x/notionists/svg?seed=${activeRequest.patient_first_name}`} alt="Patient" className="w-full h-full bg-slate-900 opacity-80 mix-blend-luminosity" />
            </div>
            
            <div className="flex items-center gap-2 text-red-400 font-black text-[10px] tracking-widest uppercase mb-3">
              <AlertCircle className="w-4 h-4" /> URGENT MATCH FOUND
            </div>
            
            <h3 className="text-xl font-serif font-bold text-white mb-2 pr-16">
              {activeRequest.patient_first_name}{activeRequest.patient_age ? `, ${activeRequest.patient_age} years old` : ""}
            </h3>
            
            <div className="flex gap-2 items-center mb-4">
              <span className={`px-2 py-0.5 border text-[10px] font-black uppercase rounded flex items-center gap-1.5 ${
                activeRequest.urgency_level === "CRITICAL" 
                  ? "bg-red-500/20 border-red-500/30 text-red-400" 
                  : activeRequest.urgency_level === "HIGH"
                  ? "bg-amber-500/20 border-amber-500/30 text-amber-400"
                  : "bg-emerald-500/20 border-emerald-500/30 text-emerald-400"
              }`}>
                {activeRequest.urgency_level === "CRITICAL" && <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
                {activeRequest.urgency_level}
              </span>
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <Heart className="w-3 h-3 text-teal-500 fill-teal-500/20" /> Your {bloodType} is a match
              </span>
            </div>

            <div className="mb-5 bg-slate-950/50 rounded-lg p-3 border border-slate-800/50">
              <div className="flex justify-between text-[10px] font-bold text-slate-400 mb-1.5 uppercase">
                <span>Compatibility</span>
                <span className="text-teal-400">{Math.round((activeRequest.compatibility_score ?? 0.5) * 100)}% Match</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.round((activeRequest.compatibility_score ?? 0.5) * 100)}%` }}
                  transition={{ duration: 1.5, delay: 0.5 }}
                  className="h-full bg-teal-500" 
                />
              </div>
            </div>

            <Button className="w-full bg-red-600 hover:bg-red-700 text-white font-bold h-12 rounded-xl text-sm shadow-lg shadow-red-900/20">
              Donate for {activeRequest.patient_first_name} →
            </Button>
          </div>
        ) : (
          <div className="bg-emerald-950/20 border border-emerald-800/30 rounded-3xl p-5 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-emerald-500/10 rounded-full flex items-center justify-center">
              <Heart className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">All Clear</h3>
            <p className="text-sm text-slate-400">No active donation requests right now. We'll notify you when someone needs your blood type.</p>
          </div>
        )}

        {/* Telegram Connection */}
        <div className={`${hasTelegram ? "bg-[#229ED9]/10 border-[#229ED9]/30" : "bg-slate-900/50 border-slate-800"} border rounded-2xl p-4 flex gap-4 items-center`}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${hasTelegram ? "bg-[#229ED9]/20" : "bg-slate-800"}`}>
            <SiTelegram className={`w-5 h-5 ${hasTelegram ? "text-[#229ED9]" : "text-slate-500 dark:text-slate-400"}`} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-sm text-slate-900 dark:text-white">Telegram Alerts</span>
              <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                hasTelegram 
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" 
                  : "bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-700"
              }`}>
                {hasTelegram ? "Connected" : "Not Connected"}
              </span>
            </div>
            {hasTelegram ? (
              <p className="text-xs text-slate-400 leading-tight">You'll receive donation requests and impact updates via @ummedrakho_bot.</p>
            ) : (
              <a href="https://t.me/ummedrakho_bot" target="_blank" rel="noopener" className="text-xs text-[#229ED9] hover:underline">
                Connect via @ummedrakho_bot →
              </a>
            )}
          </div>
        </div>

        {/* Availability Toggle (GAP-07) */}
        <div className="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 flex gap-4 items-center justify-between">
          <div>
            <div className="font-bold text-sm text-slate-900 dark:text-white mb-1">Donation Availability</div>
            <p className="text-xs text-slate-400">
              {isAvailable ? "You are active and receiving donation requests." : "Paused — you won't receive new requests."}
            </p>
          </div>
          <button
            disabled={toggleLoading}
            onClick={async () => {
              if (!donor) return;
              setToggleLoading(true);
              try {
                await setDonorAvailability(donor.donor_id, !isAvailable);
                setIsAvailable(!isAvailable);
              } finally {
                setToggleLoading(false);
              }
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-colors ${
              isAvailable
                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/30"
                : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30"
            }`}
          >
            {toggleLoading ? (
              <div className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
            ) : isAvailable ? (
              <><Pause className="w-4 h-4" /> Pause</>
            ) : (
              <><Play className="w-4 h-4" /> Resume</>
            )}
          </button>
        </div>

        {/* Badges Grid — Dynamic from API with stagger-in animation */}
        <div>
          <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider">Your Badges</h3>
          <motion.div
            className="grid grid-cols-2 gap-3"
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
          >
            {ALL_BADGES.map(badgeKey => {
              const config = BADGE_CONFIG[badgeKey];
              const isUnlocked = badges.includes(badgeKey);
              const Icon = config.icon;

              if (isUnlocked) {
                return (
                  <motion.div
                    key={badgeKey}
                    variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
                    transition={{ type: "spring", stiffness: 300, damping: 24 }}
                    whileHover={{ scale: 1.03 }}
                    className={`bg-gradient-to-br ${config.gradient} border border-${config.color}-500/30 rounded-2xl p-4 shadow-[0_4px_15px_rgba(245,158,11,0.05)]`}
                  >
                    <Icon className={`w-6 h-6 text-${config.color}-400 mb-2`} />
                    <div className="font-bold text-slate-900 dark:text-white text-sm">{config.label}</div>
                    <div className={`text-[10px] text-${config.color}-200/60 mt-1`}>{config.description}</div>
                    <div className="text-[9px] text-emerald-400 mt-2 font-bold uppercase flex items-center gap-1">✓ Unlocked</div>
                  </motion.div>
                );
              }

              return (
                <motion.div
                  key={badgeKey}
                  variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
                  transition={{ type: "spring", stiffness: 300, damping: 24 }}
                  className="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 opacity-50 grayscale relative"
                >
                  <div className="absolute top-4 right-4"><Lock className="w-3 h-3 text-slate-500 dark:text-slate-400" /></div>
                  <Icon className={`w-6 h-6 text-${config.color}-400 mb-2`} />
                  <div className="font-bold text-slate-900 dark:text-white text-sm">{config.label}</div>
                  <div className="text-[10px] text-slate-400 mt-1">{config.description}</div>
                  <div className="text-[9px] text-slate-500 dark:text-slate-400 mt-2 font-bold uppercase flex items-center gap-1">Locked</div>
                </motion.div>
              );
            })}
          </motion.div>
        </div>

        {/* M5: Health & Availability self-update (additive) + M6: Backup Areas */}
        {donor && (
          <div className="mt-6 space-y-4">
            <HealthStatusControl
              donorId={donor.donor_id}
              initialAvailable={isAvailable}
              onChange={setIsAvailable}
            />
            <LocationManager entityId={donor.donor_id} kind="donor" maxLocations={10} />
            <BloodBridgeCard entityId={donor.donor_id} kind="donor" />
          </div>
        )}

        {/* Impact Stories — from donor_memory (GAP-06) */}
        <div className="mt-8">
          <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider flex items-center gap-2">
            <HeartPulse className="w-3.5 h-3.5 text-red-400" /> Your Impact Stories
          </h3>
          {impactStories.length > 0 ? (
            <div className="space-y-3">
              {impactStories.slice(0, 3).map((story, i) => (
                <div key={i} className="bg-slate-50 dark:bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <p className="text-xs text-slate-300 leading-relaxed">{story}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-slate-50 dark:bg-slate-900/40 border border-slate-800/50 rounded-xl p-4 text-center">
              <p className="text-xs text-slate-500 dark:text-slate-400 italic">After each donation, you'll see the story of who you helped here.</p>
            </div>
          )}
        </div>

        {/* Eligibility Card */}
        {eligibility && (
          <div className={`mt-6 rounded-2xl p-4 border ${eligibility.eligible ? 'bg-emerald-950/20 border-emerald-800/30' : 'bg-amber-950/20 border-amber-800/30'}`}>
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${eligibility.eligible ? 'bg-emerald-500/20' : 'bg-amber-500/20'}`}>
                <Calendar className={`w-5 h-5 ${eligibility.eligible ? 'text-emerald-400' : 'text-amber-400'}`} />
              </div>
              <div>
                <div className="font-bold text-sm text-slate-900 dark:text-white">
                  {eligibility.eligible ? "You're eligible to donate!" : "Not yet eligible"}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  {eligibility.eligible
                    ? "You can donate blood today. Find your nearest blood bank."
                    : eligibility.days_until_eligible
                      ? `Eligible again in ${eligibility.days_until_eligible} days`
                      : eligibility.reason || "Please check with your doctor."}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* City Leaderboard */}
        {leaderboard.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider flex items-center gap-2">
              <Trophy className="w-3.5 h-3.5 text-amber-400" /> City Leaderboard — {donor?.city}
            </h3>
            <div className="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
              {leaderboard.map((entry, i) => (
                <div key={i} className={`flex items-center gap-3 px-4 py-3 ${i !== leaderboard.length - 1 ? 'border-b border-slate-800/50' : ''} ${entry.name === donor?.name ? 'bg-teal-950/20' : ''}`}>
                  <span className={`w-6 h-6 flex items-center justify-center rounded-full text-[10px] font-black ${i < 3 ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-400'}`}>
                    {entry.rank}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">{entry.name}</div>
                    <div className="text-[10px] text-slate-500">{entry.lives_saved} lives · {entry.donation_count} donations</div>
                  </div>
                  <div className="flex gap-1">
                    {entry.badges.slice(0, 2).map(b => {
                      const cfg = BADGE_CONFIG[b];
                      if (!cfg) return null;
                      const Icon = cfg.icon;
                      return <Icon key={b} className={`w-3.5 h-3.5 text-${cfg.color}-400`} />;
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* DPDP Privacy & Consent (§11, §12) */}
        <div className="mt-6">
          <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-purple-400" /> Privacy & Consent (DPDP 2023)
          </h3>
          <div className="bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 space-y-4">
            {/* Consent Status */}
            {consent && consent.consents && (
              <div className="space-y-2">
                <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Your Consents</div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(consent.consents || {}).map(([key, status]) => (
                    <div key={key} className="flex items-center justify-between bg-slate-800/50 rounded-lg px-3 py-2">
                      <span className="text-[11px] text-slate-300 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${status === 'granted' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                        {status}
                      </span>
                    </div>
                  ))}
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full mt-2 text-xs border-red-800/50 text-red-400 hover:bg-red-950/30"
                  disabled={privacyLoading === 'revoke'}
                  onClick={async () => {
                    if (!donor) return;
                    setPrivacyLoading('revoke');
                    try {
                      await revokeConsent(donor.donor_id, "all");
                      const updated = await getConsentSummary(donor.donor_id);
                      setConsent(updated);
                    } catch {} finally { setPrivacyLoading(null); }
                  }}
                >
                  {privacyLoading === 'revoke' ? 'Revoking...' : 'Revoke All Consents'}
                </Button>
              </div>
            )}

            {/* Data Actions */}
            <div className="flex gap-2 pt-2 border-t border-slate-800/50">
              <Button
                size="sm"
                variant="outline"
                className="flex-1 text-xs gap-1.5 border-slate-700 text-slate-300 hover:bg-slate-800"
                disabled={privacyLoading === 'export'}
                onClick={async () => {
                  if (!donor) return;
                  setPrivacyLoading('export');
                  try {
                    const data = await exportDonorData(donor.donor_id);
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url; a.download = `my-data-${donor.donor_id}.json`; a.click();
                    URL.revokeObjectURL(url);
                  } catch {} finally { setPrivacyLoading(null); }
                }}
              >
                <Download className="w-3.5 h-3.5" /> {privacyLoading === 'export' ? 'Exporting...' : 'Export My Data'}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="flex-1 text-xs gap-1.5 border-red-900/50 text-red-400 hover:bg-red-950/30"
                disabled={privacyLoading === 'erase'}
                onClick={async () => {
                  if (!donor) return;
                  if (!confirm("Are you sure? This will permanently delete all your data. This cannot be undone.")) return;
                  setPrivacyLoading('erase');
                  try {
                    await eraseDonorData(donor.donor_id);
                    localStorage.removeItem("donor_id");
                    localStorage.removeItem("auth_token");
                    window.location.href = "/";
                  } catch {} finally { setPrivacyLoading(null); }
                }}
              >
                <Trash2 className="w-3.5 h-3.5" /> {privacyLoading === 'erase' ? 'Deleting...' : 'Delete My Account'}
              </Button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}