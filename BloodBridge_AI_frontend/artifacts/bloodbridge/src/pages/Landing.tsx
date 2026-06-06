import { useState, useEffect } from "react";
import { Link } from "wouter";
import { ArrowRight, Activity, Network, Shield, Droplet, Users, Globe, Database, Cpu, LayoutDashboard, Smartphone, HeartPulse, GitBranch, Target, Megaphone, Table2, Moon, Sun, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import CountUp from "react-countup";
import InteractiveArchitecture from "../components/InteractiveArchitecture";
import { useTheme } from "@/lib/theme";

const TICKER_ITEMS = [
  "Telegram Bot → AI Routing", "Neo4j Blood Bridge Chains", "8-Antigen Compatibility",
  "XGBoost Churn Prediction", "Gemini Conflict Resolver", "AI Voice Calls · Twilio",
  "e-RaktKosh Integration", "10+ Indian Languages", "₹0 Deployment"
];

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

export default function Landing() {
  const { isDark, toggleDark } = useTheme();
  const isLightMode = !isDark;
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className={`min-h-screen font-sans transition-colors duration-700 pb-20 ${isLightMode
      ? "bg-[#FAFAFA] text-[#1A1A1C] selection:bg-[#C8102E] selection:text-white"
      : "bg-[#050505] text-white selection:bg-[#C8102E] selection:text-white"
      }`}>
      {/* Sticky Navbar */}
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className={`fixed top-0 w-full z-50 backdrop-blur-xl border-b transition-colors duration-500 ${isLightMode
          ? "bg-[rgba(250,250,250,0.8)] border-[#E8E0D8] shadow-sm"
          : "bg-[#050505]/80 border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.5)]"
          }`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 cursor-pointer group">
            <div className="w-7 h-7 bg-gradient-to-br from-[#C8102E] to-[#EF4444] rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
              <div className="w-1.5 h-1.5 bg-white rounded-full -rotate-45" />
            </div>
            <span className="font-serif font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-[#C8102E] to-[#EF4444]">inquilab AI</span>
          </Link>
          <div className={`hidden md:flex gap-8 text-[12px] font-bold tracking-[0.2em] uppercase ${isLightMode ? "text-[#6B6572]" : "text-[#888890]"}`}>
            <a href="#features" className={`transition-all hover:-translate-y-0.5 ${isLightMode ? "hover:text-[#1A1A1C]" : "hover:text-white"}`}>Features</a>
            <a href="#architecture" className={`transition-all hover:-translate-y-0.5 ${isLightMode ? "hover:text-[#1A1A1C]" : "hover:text-white"}`}>Architecture</a>
            <a href="#agents" className={`transition-all hover:-translate-y-0.5 ${isLightMode ? "hover:text-[#1A1A1C]" : "hover:text-white"}`}>Agents</a>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://t.me/ummedrakho_bot" target="_blank" rel="noopener" className="flex items-center gap-1.5 text-[#229ED9] hover:text-[#1DA1F2] transition-colors" title="Join via Telegram">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
              <span className="text-xs font-medium hidden sm:inline">Telegram</span>
            </a>
            <Link href="/patient/login" className={`text-sm font-medium transition-colors ${isLightMode ? "text-[#4B4B55] hover:text-[#1A1A1C]" : "text-white/70 hover:text-white"}`}>Patient</Link>
            <Link href="/donor/login" className={`text-sm font-medium transition-colors ${isLightMode ? "text-[#4B4B55] hover:text-[#1A1A1C]" : "text-white/70 hover:text-white"}`}>Donor</Link>
            <Link href="/login" className={`text-sm font-medium transition-colors hidden sm:block ${isLightMode ? "text-[#4B4B55] hover:text-[#1A1A1C]" : "text-white/70 hover:text-white"}`}>Staff Login</Link>

            <button
              onClick={toggleDark}
              className={`relative flex items-center justify-between w-12 h-6 rounded-full p-1 transition-colors ${isLightMode ? 'bg-[#E8E0D8] hover:bg-[#d4cdc4]' : 'bg-white/10 hover:bg-white/20'}`}
              aria-label="Toggle Theme"
            >
              <div className="flex w-full justify-between px-0.5 z-0">
                <Moon className="w-3.5 h-3.5 text-[#1A1A1C]" />
                <Sun className="w-3.5 h-3.5 text-white" />
              </div>
              <motion.div
                className={`absolute w-4 h-4 rounded-full shadow-sm z-10 ${isLightMode ? 'bg-white' : 'bg-[#1A1A1C]'}`}
                animate={{ left: isLightMode ? 4 : 28 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            </button>

            <Link href="/dashboard/emergency" className="text-sm font-medium bg-gradient-to-r from-[#C8102E] to-[#E11D48] text-white px-5 py-2 rounded-full hover:shadow-[0_0_20px_rgba(200,16,46,0.4)] transition-all hover:-translate-y-0.5">
              View Demo
            </Link>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 min-h-[95vh] flex flex-col justify-center overflow-hidden">
        {/* Animated Background Grid */}
        <div className={`absolute inset-0 z-0 opacity-30 pointer-events-none transition-opacity duration-1000 ${isLightMode ? "bg-[rgba(0,0,0,0.02)]" : ""}`}
          style={{
            backgroundImage: isLightMode
              ? 'linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px)'
              : 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }} />

        {/* Glow Blobs */}
        <motion.div
          animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className={`absolute top-1/2 left-[80%] -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[radial-gradient(ellipse_60%_80%_at_70%_50%,${isLightMode ? 'rgba(200,16,46,0.08)' : 'rgba(200,16,46,0.15)'},transparent)] z-0 pointer-events-none blur-3xl`}
        />
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.4, 0.2] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className={`absolute top-[20%] left-[20%] -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[radial-gradient(ellipse_50%_50%_at_50%_50%,${isLightMode ? 'rgba(13,148,136,0.05)' : 'rgba(20,241,217,0.1)'},transparent)] z-0 pointer-events-none blur-3xl`}
        />

        {/* Canvas Particles Mockup */}
        <div className={`absolute inset-0 z-0 overflow-hidden pointer-events-none ${isLightMode ? "opacity-30" : "opacity-40"}`}>
          {Array.from({ length: 30 }).map((_, i) => (
            <motion.div
              key={i}
              initial={{ y: Math.random() * 100, x: Math.random() * 100, opacity: Math.random() }}
              animate={{ y: [null, Math.random() * -100], opacity: [null, Math.random(), 0] }}
              transition={{ duration: 10 + Math.random() * 20, repeat: Infinity, ease: "linear" }}
              className={`absolute w-1 h-1 rounded-full blur-[1px] ${i % 3 === 0 ? "bg-[#C8102E]" : i % 3 === 1 ? "bg-[#14F1D9]" : "bg-[#F59E0B]"}`}
              style={{
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
              }}
            />
          ))}
        </div>

        <div className="max-w-7xl mx-auto w-full relative z-10 grid md:grid-cols-2 gap-12 items-center">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="flex flex-col items-start gap-6"
          >
            <motion.div variants={fadeUp} className={`px-4 py-1.5 border rounded-full text-xs font-mono font-bold flex items-center gap-2 shadow-sm ${isLightMode ? "border-[#E8E0D8] text-[#C8102E] bg-white" : "border-[#C8102E]/30 text-[#C8102E] bg-[#C8102E]/10"}`}>
              <Sparkles className="w-3.5 h-3.5" />
                AI FOR BLOOD DONATION
            </motion.div>

            <motion.h1 variants={fadeUp} className="font-serif font-black text-6xl md:text-8xl leading-[1.05] tracking-tight">
              Save lives with<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#C8102E] to-[#F43F5E] italic font-serif">agentic AI.</span><br />

            </motion.h1>

            <motion.p variants={fadeUp} className={`text-lg max-w-lg leading-relaxed font-light ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>
              The world's first autonomous coordination system for Thalassemia patients. Combining <span className={`font-medium ${isLightMode ? "text-black" : "text-white"}`}>LangGraph</span>, <span className={`font-medium ${isLightMode ? "text-black" : "text-white"}`}>Neo4j</span>, and predictive ML into an open-source swarm.
            </motion.p>

            <motion.div variants={fadeUp} className="flex flex-wrap gap-4 pt-6">
              <Link href="/dashboard/emergency" className="bg-gradient-to-r from-[#C8102E] to-[#E11D48] text-white px-8 py-4 rounded-full font-medium flex items-center gap-2 hover:shadow-[0_0_30px_rgba(200,16,46,0.5)] transition-all hover:-translate-y-1 text-lg">
                Start Live Demo <ArrowRight className="w-5 h-5" />
              </Link>
              <a href="#architecture" className={`px-8 py-4 rounded-full font-medium border transition-all hover:-translate-y-1 text-lg backdrop-blur-sm ${isLightMode ? "border-[#C8102E]/20 text-[#1A1A1C] hover:bg-[#C8102E]/5" : "border-white/20 text-white hover:bg-white/10"}`}>
                Explore Architecture
              </a>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
            className="relative h-[500px] hidden md:flex items-center justify-center perspective-[1000px]"
          >
            <div className={`absolute inset-0 bg-gradient-to-tr ${isLightMode ? "from-[#C8102E]/5 to-[#14F1D9]/5" : "from-[#C8102E]/10 to-[#14F1D9]/10"} rounded-full blur-3xl`} />
            <motion.div
              animate={{ rotateY: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              className="relative z-10 w-full h-full flex items-center justify-center transform-style-3d"
            >
              <Network className={`w-72 h-72 drop-shadow-2xl ${isLightMode ? "text-[#C8102E]" : "text-white"}`} strokeWidth={0.5} />
              <motion.div
                animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 bg-[#C8102E] rounded-full blur-xl"
              />
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats Strip */}
      <section className={`border-y relative overflow-hidden transition-colors duration-500 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-[#0A0A0C] border-white/10"}`}>
        <div className={`absolute inset-0 ${isLightMode ? "bg-gradient-to-r from-transparent via-[#F9F5F0] to-transparent" : "bg-gradient-to-r from-transparent via-white/5 to-transparent"}`} />
        <div className={`max-w-7xl mx-auto px-6 py-16 grid grid-cols-2 md:grid-cols-4 gap-8 divide-x relative z-10 text-center md:text-left ${isLightMode ? "divide-[#E8E0D8]" : "divide-white/10"}`}>
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="px-4 flex flex-col justify-center items-center md:items-start">
            <div className="font-serif font-bold text-5xl text-transparent bg-clip-text bg-gradient-to-r from-[#C8102E] to-[#EF4444] mb-2 flex items-center">
              <CountUp end={1} duration={2} decimals={0} /><span className="ml-1">L+</span>
            </div>
            <div className={`text-[11px] uppercase tracking-[0.2em] font-bold ${isLightMode ? "text-[#6B6572]" : "text-white/40"}`}>Thalassemia patients</div>
          </motion.div>
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="px-4 flex flex-col justify-center items-center md:items-start">
            <div className="font-serif font-bold text-5xl text-transparent bg-clip-text bg-gradient-to-r from-[#0D9488] to-[#14F1D9] mb-2 flex items-center">
              <CountUp end={500} duration={2.5} />–<CountUp end={700} duration={3} />
            </div>
            <div className={`text-[11px] uppercase tracking-[0.2em] font-bold ${isLightMode ? "text-[#6B6572]" : "text-white/40"}`}>Transfusions / lifetime</div>
          </motion.div>
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="px-4 flex flex-col justify-center items-center md:items-start">
            <div className="font-serif font-bold text-5xl text-transparent bg-clip-text bg-gradient-to-r from-[#F59E0B] to-[#FBBF24] mb-2">
              <CountUp end={14} duration={2} />
            </div>
            <div className={`text-[11px] uppercase tracking-[0.2em] font-bold ${isLightMode ? "text-[#6B6572]" : "text-white/40"}`}>LangGraph AI agents</div>
          </motion.div>
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="px-4 flex flex-col justify-center items-center md:items-start">
            <div className="font-serif font-bold text-5xl text-transparent bg-clip-text bg-gradient-to-r from-[#10B981] to-[#34D399] mb-2 flex items-center">
              ₹<CountUp end={0} duration={1} />
            </div>
            <div className={`text-[11px] uppercase tracking-[0.2em] font-bold ${isLightMode ? "text-[#6B6572]" : "text-white/40"}`}>Total deployment cost</div>
          </motion.div>
        </div>
      </section>

      {/* Scrolling Ticker */}
      <section className={`overflow-hidden py-5 relative transition-colors duration-500 ${isLightMode ? "bg-[#C8102E] text-white" : "bg-[#C8102E]/10 border-b border-[#C8102E]/20 text-[#C8102E]"}`}>
        <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-[currentColor] to-transparent z-10" style={{ color: isLightMode ? '#C8102E' : '#050505' }} />
        <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-[currentColor] to-transparent z-10" style={{ color: isLightMode ? '#C8102E' : '#050505' }} />
        <div className="flex whitespace-nowrap animate-[marquee_30s_linear_infinite] items-center">
          {TICKER_ITEMS.concat(TICKER_ITEMS).map((item, i) => (
            <div key={i} className="flex items-center text-[13px] font-mono uppercase tracking-wider font-bold">
              <span className="mx-8 opacity-50">✦</span>
              {item}
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Section */}
      <section id="architecture" className={`py-32 px-6 relative transition-colors ${isLightMode ? "bg-[#F9F5F0]" : "bg-[#050505]"}`}>
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase mb-6 border border-[#C8102E]/20 text-[#C8102E] bg-[#C8102E]/5">
              <Database className="w-3.5 h-3.5" /> System Architecture
            </div>
            <h2 className="font-serif font-bold text-5xl mb-6">How it's built</h2>
            <p className={`max-w-2xl mx-auto text-lg mb-2 font-light ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>
              An interactive visualization of the components and data flows that power the inquilab AI platform.
            </p>
            <p className={`text-sm ${isLightMode ? "text-[#1A1A1C]" : "text-[#14F1D9]"} font-medium animate-pulse`}>Click and drag to pan. Scroll to zoom.</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className={`mb-32 rounded-2xl overflow-hidden shadow-2xl border backdrop-blur-sm ${isLightMode ? "border-[#E8E0D8] bg-white/50" : "border-white/10 bg-[#111116]/50 shadow-[0_0_50px_rgba(200,16,46,0.1)]"}`}
          >
            <InteractiveArchitecture />
          </motion.div>

          <div className="space-y-32">
            {/* Deep Dive Pillars */}
            <div>
              <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="text-center mb-16">
                <h3 className="text-4xl font-serif font-bold mb-4">Core Architecture Pillars</h3>
                <p className={`text-lg font-light ${isLightMode ? "text-[#4B4B55]" : "text-white/50"}`}>The four foundational layers of the agentic swarm.</p>
              </motion.div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Pillar A */}
                <motion.div
                  initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
                  className="relative p-[1px] rounded-[26px] overflow-hidden group hover:-translate-y-2 transition-transform duration-500 hover:shadow-[0_10px_40px_rgba(13,148,136,0.2)]"
                >
                  <div className={`absolute inset-[-100%] animate-[spin_4s_linear_infinite] opacity-50 group-hover:opacity-100 transition-opacity duration-500 bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0%,#0D9488_50%,transparent_100%)]`} />
                  <div className={`relative h-full p-10 rounded-3xl overflow-hidden ${isLightMode ? "bg-[#FFFFFF]" : "bg-[#0A0A0C]"}`}>
                    <div className={`absolute -top-24 -right-24 w-64 h-64 blur-[100px] rounded-full opacity-40 transition-opacity group-hover:opacity-100 ${isLightMode ? "bg-[#0D9488]/30" : "bg-[#0D9488]/30"}`} />
                    <h4 className="text-[#0D9488] font-bold text-xs tracking-[0.2em] uppercase mb-4 flex items-center gap-2"><Target className="w-4 h-4" /> Pillar A</h4>
                    <h5 className="text-3xl font-serif font-bold mb-8">Smart Matching</h5>
                    <ul className="space-y-6 relative z-10">
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#0D9488]/10 text-[#0D9488]" : "bg-[#0D9488]/20 text-[#0D9488]"}`}><Globe className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>Geo Radius-Tier Matching</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Haversine concentric ring expansion (5km, 15km, 30km) prioritizing proximity with Multi-Location support for donors.</span>
                        </div>
                      </li>
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#0D9488]/10 text-[#0D9488]" : "bg-[#0D9488]/20 text-[#0D9488]"}`}><Activity className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>Weighted Multi-Criteria Scoring</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Ranks donors by transparent weights: ABO+Rh match, proximity, engagement history, and eligibility freshness.</span>
                        </div>
                      </li>
                    </ul>
                  </div>
                </motion.div>

                {/* Pillar B */}
                <motion.div
                  initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
                  className="relative p-[1px] rounded-[26px] overflow-hidden group hover:-translate-y-2 transition-transform duration-500 hover:shadow-[0_10px_40px_rgba(200,16,46,0.2)]"
                >
                  <div className={`absolute inset-[-100%] animate-[spin_4s_linear_infinite] opacity-50 group-hover:opacity-100 transition-opacity duration-500 bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0%,#C8102E_50%,transparent_100%)]`} />
                  <div className={`relative h-full p-10 rounded-3xl overflow-hidden ${isLightMode ? "bg-[#FFFFFF]" : "bg-[#0A0A0C]"}`}>
                    <div className={`absolute -top-24 -right-24 w-64 h-64 blur-[100px] rounded-full opacity-40 transition-opacity group-hover:opacity-100 ${isLightMode ? "bg-[#C8102E]/20" : "bg-[#C8102E]/20"}`} />
                    <h4 className="text-[#C8102E] font-bold text-xs tracking-[0.2em] uppercase mb-4 flex items-center gap-2"><GitBranch className="w-4 h-4" /> Pillar B</h4>
                    <h5 className="text-3xl font-serif font-bold mb-8">Care Coordination</h5>
                    <ul className="space-y-6 relative z-10">
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#C8102E]/10 text-[#C8102E]" : "bg-[#C8102E]/20 text-[#C8102E]"}`}><Cpu className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>14-Node LangGraph Pipeline</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Autonomous parallel graph routing, evaluating urgency, antigen score, match criteria, and orchestrating full outreach.</span>
                        </div>
                      </li>
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#C8102E]/10 text-[#C8102E]" : "bg-[#C8102E]/20 text-[#C8102E]"}`}><Megaphone className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>AI Voice + Fallbacks</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Bolna.ai local-language calls for unresponsive nodes with natural language intent capture, falling back to Twilio SMS.</span>
                        </div>
                      </li>
                    </ul>
                  </div>
                </motion.div>

                {/* Pillar C */}
                <motion.div
                  initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
                  className="relative p-[1px] rounded-[26px] overflow-hidden group hover:-translate-y-2 transition-transform duration-500 hover:shadow-[0_10px_40px_rgba(16,185,129,0.2)]"
                >
                  <div className={`absolute inset-[-100%] animate-[spin_4s_linear_infinite] opacity-50 group-hover:opacity-100 transition-opacity duration-500 bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0%,#10B981_50%,transparent_100%)]`} />
                  <div className={`relative h-full p-10 rounded-3xl overflow-hidden ${isLightMode ? "bg-[#FFFFFF]" : "bg-[#0A0A0C]"}`}>
                    <div className={`absolute -top-24 -right-24 w-64 h-64 blur-[100px] rounded-full opacity-40 transition-opacity group-hover:opacity-100 ${isLightMode ? "bg-[#10B981]/20" : "bg-[#10B981]/20"}`} />
                    <h4 className="text-[#10B981] font-bold text-xs tracking-[0.2em] uppercase mb-4 flex items-center gap-2"><Users className="w-4 h-4" /> Pillar C</h4>
                    <h5 className="text-3xl font-serif font-bold mb-8">Engagement</h5>
                    <ul className="space-y-6 relative z-10">
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#10B981]/10 text-[#10B981]" : "bg-[#10B981]/20 text-[#10B981]"}`}><Target className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>XGBoost Churn Prediction</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Predicts inactivity risk using genuine NGO metrics (call-to-donation ratio) to trigger 4 tiers of automated intervention.</span>
                        </div>
                      </li>
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#10B981]/10 text-[#10B981]" : "bg-[#10B981]/20 text-[#10B981]"}`}><Smartphone className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>Agentic Telegram Bot</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Tool-calling LLM providing contextual memory, multilanguage conversational support, and dynamic feature execution.</span>
                        </div>
                      </li>
                    </ul>
                  </div>
                </motion.div>

                {/* Pillar D */}
                <motion.div
                  initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
                  className="relative p-[1px] rounded-[26px] overflow-hidden group hover:-translate-y-2 transition-transform duration-500 hover:shadow-[0_10px_40px_rgba(245,158,11,0.2)]"
                >
                  <div className={`absolute inset-[-100%] animate-[spin_4s_linear_infinite] opacity-50 group-hover:opacity-100 transition-opacity duration-500 bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0%,#F59E0B_50%,transparent_100%)]`} />
                  <div className={`relative h-full p-10 rounded-3xl overflow-hidden ${isLightMode ? "bg-[#FFFFFF]" : "bg-[#0A0A0C]"}`}>
                    <div className={`absolute -top-24 -right-24 w-64 h-64 blur-[100px] rounded-full opacity-40 transition-opacity group-hover:opacity-100 ${isLightMode ? "bg-[#F59E0B]/20" : "bg-[#F59E0B]/20"}`} />
                    <h4 className="text-[#F59E0B] font-bold text-xs tracking-[0.2em] uppercase mb-4 flex items-center gap-2"><Shield className="w-4 h-4" /> Pillar D</h4>
                    <h5 className="text-3xl font-serif font-bold mb-8">Scale & Integrity</h5>
                    <ul className="space-y-6 relative z-10">
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#F59E0B]/10 text-[#F59E0B]" : "bg-[#F59E0B]/20 text-[#F59E0B]"}`}><Network className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>Tiered LLM Architecture</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Cost-optimized tiering across Fast Models (Telegram replies), Reasoning Models, and Quality Models.</span>
                        </div>
                      </li>
                      <li className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${isLightMode ? "bg-[#F59E0B]/10 text-[#F59E0B]" : "bg-[#F59E0B]/20 text-[#F59E0B]"}`}><Shield className="w-5 h-5" /></div>
                        <div>
                          <strong className={`block text-lg font-bold mb-1 ${isLightMode ? "text-[#1A1A1C]" : "text-white"}`}>DPDP 2023 Compliance</strong>
                          <span className={`text-sm leading-relaxed ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>Strict Row Level Security, data obfuscation, explicit consent gating, and fully anonymized patient impact stories.</span>
                        </div>
                      </li>
                    </ul>
                  </div>
                </motion.div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Agents Swarm */}
      <section id="agents" className={`py-32 px-6 border-y relative overflow-hidden transition-colors ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-[#050505] border-white/10"}`}>
        <div className={`absolute inset-0 z-0 pointer-events-none opacity-50 ${isLightMode ? "bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.02)_1px,transparent_1px)]" : "bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.02)_1px,transparent_1px)]"}`} style={{ backgroundSize: '24px 24px' }} />
        <div className="text-center mb-16 relative z-10">
          <h2 className="font-serif font-bold text-5xl mb-6">The Multi-Agent Swarm</h2>
          <p className={`max-w-2xl mx-auto text-lg font-light ${isLightMode ? "text-[#6B6572]" : "text-white/60"}`}>inquilab AI utilizes a specialized LangGraph architecture where agents coordinate autonomously to resolve supply constraints in real-time.</p>
        </div>
        <div className="flex flex-wrap justify-center gap-4 max-w-5xl mx-auto relative z-10">
          {["MatchingAgent", "PlannerAgent", "OutreachAgent", "ChainMonitorAgent", "ChainRepairAgent", "VoiceAgent", "GamificationAgent", "OutcomeAgent"].map((agent, i) => (
            <motion.div
              key={agent}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, type: "spring", bounce: 0.4 }}
              whileHover={{ scale: 1.05, y: -5 }}
              className={`px-6 py-3 border rounded-full text-sm font-mono font-bold transition-shadow shadow-sm cursor-default ${isLightMode ? "bg-white border-[#E8E0D8] text-[#1A1A1C] hover:shadow-md hover:border-[#C8102E]/30" : "bg-[#111116] border-white/10 text-white/80 hover:shadow-[0_0_15px_rgba(200,16,46,0.3)] hover:border-[#C8102E]/50"}`}
            >
              {agent}
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className={`py-32 px-6 text-center relative overflow-hidden transition-colors duration-700 ${isLightMode ? "bg-[#F9F5F0]" : "bg-[#0A0A0C]"}`}>
        <motion.div
          initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}
          className="relative z-10"
        >
          <h2 className="font-serif text-5xl md:text-7xl font-bold mb-10 tracking-tight">Ready to see it in action?</h2>
          <Link href="/dashboard/emergency" className="inline-flex bg-gradient-to-r from-[#C8102E] to-[#E11D48] text-white px-10 py-5 rounded-full font-bold text-xl items-center gap-3 hover:shadow-[0_0_40px_rgba(200,16,46,0.6)] transition-all hover:-translate-y-2 mb-16">
            Open Operations Center <ArrowRight className="w-6 h-6" />
          </Link>
          <div className={`flex flex-wrap justify-center gap-8 text-sm font-mono font-bold tracking-widest uppercase ${isLightMode ? "text-[#6B6572]" : "text-white/40"}`}>
            <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" /> Status: Online</span>
            <span>Mock Data: True</span>
            <span>License: Open Source</span>
          </div>
        </motion.div>
      </section>
    </div>
  );
}