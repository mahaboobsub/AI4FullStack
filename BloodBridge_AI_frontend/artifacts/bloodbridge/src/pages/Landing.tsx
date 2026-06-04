import { useState } from "react";
import { Link } from "wouter";
import { ArrowRight, Activity, Network, Shield, Droplet, Users, Globe, Database, Cpu, LayoutDashboard, Smartphone, HeartPulse, GitBranch, Target, Megaphone, Table2, Moon, Sun } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const TICKER_ITEMS = [
  "Telegram Bot → AI Routing", "Neo4j Blood Bridge Chains", "8-Antigen Compatibility",
  "XGBoost Churn Prediction", "Gemini Conflict Resolver", "AI Voice Calls · Twilio",
  "e-RaktKosh Integration", "10+ Indian Languages", "₹0 Deployment"
];

export default function Landing() {
  const [isLightMode, setIsLightMode] = useState(false);

  return (
    <div className={`min-h-screen font-sans transition-colors duration-500 pb-20 ${
      isLightMode 
        ? "bg-[#F9F5F0] text-[#1A1A1C] selection:bg-[#C8102E] selection:text-white" 
        : "bg-[#0A0A0C] text-white selection:bg-[#C8102E] selection:text-white"
    }`}>
      {/* Sticky Navbar */}
      <nav className={`fixed top-0 w-full z-50 backdrop-blur-md border-b transition-colors duration-500 ${
        isLightMode 
          ? "bg-[rgba(249,245,240,0.95)] border-[#E8E0D8]" 
          : "bg-[#0A0A0C]/95 border-white/10"
      }`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-[#C8102E] rounded-tl-full rounded-tr-full rounded-bl-full rounded-br-none rotate-45 flex items-center justify-center">
              <div className="w-1.5 h-1.5 bg-white rounded-full -rotate-45" />
            </div>
            <span className="font-serif font-bold text-lg tracking-tight">BloodBridge AI</span>
          </div>
          <div className={`hidden md:flex gap-8 text-[13px] font-medium tracking-widest uppercase ${isLightMode ? "text-[#6B6572]" : "text-[#6B6B72]"}`}>
            <a href="#features" className={`transition-colors ${isLightMode ? "hover:text-[#1A1A1C]" : "hover:text-white"}`}>Features</a>
            <a href="#architecture" className={`transition-colors ${isLightMode ? "hover:text-[#1A1A1C]" : "hover:text-white"}`}>Architecture</a>
            <a href="#agents" className={`transition-colors ${isLightMode ? "hover:text-[#1A1A1C]" : "hover:text-white"}`}>Agents</a>
            <a href="#dashboard" className={`transition-colors ${isLightMode ? "hover:text-[#1A1A1C]" : "hover:text-white"}`}>Dashboard</a>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/patient/login" className={`text-sm font-medium transition-colors ${isLightMode ? "text-[#4B4B55] hover:text-[#1A1A1C]" : "text-white/70 hover:text-white"}`}>Patient</Link>
            <Link href="/donor/login" className={`text-sm font-medium transition-colors ${isLightMode ? "text-[#4B4B55] hover:text-[#1A1A1C]" : "text-white/70 hover:text-white"}`}>Donor</Link>
            <Link href="/login" className={`text-sm font-medium transition-colors ${isLightMode ? "text-[#4B4B55] hover:text-[#1A1A1C]" : "text-white/70 hover:text-white"}`}>Staff Login</Link>
            
            <button 
              onClick={() => setIsLightMode(!isLightMode)}
              className={`relative flex items-center justify-between w-12 h-6 rounded-full p-1 transition-colors ${isLightMode ? 'bg-[#E8E0D8]' : 'bg-white/10'}`}
            >
              <div className="flex w-full justify-between px-0.5 z-0">
                <Moon className="w-3.5 h-3.5 text-[#1A1A1C]" />
                <Sun className="w-3.5 h-3.5 text-white" />
              </div>
              <motion.div 
                layout
                className={`absolute top-1 bottom-1 w-4 rounded-full z-10 ${isLightMode ? 'bg-white left-1' : 'bg-[#1A1A1C] right-1'}`}
              />
            </button>

            <Link href="/dashboard/emergency" className="text-sm font-medium bg-[#C8102E] text-white px-5 py-2 rounded-[4px] hover:bg-[#A00D24] transition-colors shadow-sm">
              View Demo
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 min-h-[90vh] flex flex-col justify-center overflow-hidden">
        <div className={`absolute inset-0 z-0 opacity-20 pointer-events-none ${isLightMode ? "bg-[rgba(0,0,0,0.03)]" : ""}`} 
             style={{ 
               backgroundImage: isLightMode 
                 ? 'linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px)' 
                 : 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)', 
               backgroundSize: '40px 40px' 
             }} />
        <div className={`absolute top-1/2 left-[70%] -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[radial-gradient(ellipse_60%_80%_at_70%_50%,${isLightMode ? 'rgba(200,16,46,0.06)' : 'rgba(200,16,46,0.12)'},transparent)] z-0 pointer-events-none`} />
        
        {/* Canvas Particles Mockup */}
        <div className={`absolute inset-0 z-0 overflow-hidden pointer-events-none ${isLightMode ? "opacity-40" : "opacity-40"}`}>
          {Array.from({ length: 20 }).map((_, i) => (
            <div key={i} className={`absolute w-1.5 h-1.5 rounded-full blur-[1px] ${isLightMode ? "bg-[#C8102E]" : "bg-[#14F1D9]"}`} style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animation: `pulse ${2 + Math.random() * 3}s infinite alternate`
            }} />
          ))}
        </div>

        <div className="max-w-7xl mx-auto w-full relative z-10 grid md:grid-cols-2 gap-12 items-center">
          <div className="flex flex-col items-start gap-6">
            <div className={`px-3 py-1 border rounded-full text-xs font-mono flex items-center gap-2 ${isLightMode ? "border-[#E8E0D8] text-[#6B6572]" : "border-white/10 text-white/70"}`}>
              <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${isLightMode ? "bg-[#C8102E]" : "bg-[#14F1D9]"}`} />
              BLEND360 HACKATHON · AI FOR BLOOD DONATION
            </div>
            <h1 className="font-serif font-black text-5xl md:text-7xl leading-[1.1] tracking-tight">
              Save lives with<br />
              <span className="text-[#C8102E] italic font-serif">agentic AI.</span><br />
              At zero cost.
            </h1>
            <p className={`text-lg max-w-lg leading-relaxed font-light ${isLightMode ? "text-[#4B4B55]" : "text-white/55"}`}>
              Autonomous coordination system for Thalassemia patients. Connects patients with compatible donors via LangGraph agents, Telegram, and Neo4j.
            </p>
            <div className="flex gap-4 pt-4">
              <Link href="/dashboard/emergency" className="bg-[#C8102E] text-white px-6 py-3 rounded-[4px] font-medium flex items-center gap-2 hover:bg-[#A00D24] transition-colors shadow-md">
                Live Demo <ArrowRight className="w-4 h-4" />
              </Link>
              <a href="#architecture" className={`px-6 py-3 rounded-[4px] font-medium border transition-colors ${isLightMode ? "border-[#C8102E]/40 text-[#1A1A1C] hover:bg-[#E8E0D8]" : "border-white/10 hover:bg-white/5"}`}>
                Architecture
              </a>
            </div>
          </div>
          <div className="relative h-[400px] hidden md:block">
            <div className="absolute inset-0 flex items-center justify-center">
              <Network className={`w-64 h-64 opacity-20 ${isLightMode ? "text-[#C8102E]" : "text-[#14F1D9]"}`} strokeWidth={1} />
            </div>
          </div>
        </div>
      </section>

      {/* Stats Strip */}
      <section className={`border-y transition-colors duration-500 ${isLightMode ? "bg-[#F0EAE2] border-[#E8E0D8]" : "bg-[#111116] border-white/10"}`}>
        <div className={`max-w-7xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8 divide-x text-center md:text-left ${isLightMode ? "divide-[#E8E0D8]" : "divide-white/10"}`}>
          <div className="px-4">
            <div className="font-serif font-bold text-4xl text-[#C8102E] mb-2">1L+</div>
            <div className={`text-sm uppercase tracking-wider font-medium ${isLightMode ? "text-[#6B6572]" : "text-white/50"}`}>Thalassemia patients</div>
          </div>
          <div className="px-4">
            <div className="font-serif font-bold text-4xl text-[#C8102E] mb-2">500–700</div>
            <div className={`text-sm uppercase tracking-wider font-medium ${isLightMode ? "text-[#6B6572]" : "text-white/50"}`}>Transfusions / lifetime</div>
          </div>
          <div className="px-4">
            <div className="font-serif font-bold text-4xl text-[#C8102E] mb-2">14</div>
            <div className={`text-sm uppercase tracking-wider font-medium ${isLightMode ? "text-[#6B6572]" : "text-white/50"}`}>LangGraph AI agents</div>
          </div>
          <div className="px-4">
            <div className="font-serif font-bold text-4xl text-[#C8102E] mb-2">₹0</div>
            <div className={`text-sm uppercase tracking-wider font-medium ${isLightMode ? "text-[#6B6572]" : "text-white/50"}`}>Total deployment cost</div>
          </div>
        </div>
      </section>

      {/* Scrolling Ticker */}
      <section className={`overflow-hidden border-b py-4 transition-colors duration-500 ${isLightMode ? "bg-[#EDE6DC] border-[#E8E0D8]" : "bg-[#0A0A0C] border-white/10"}`}>
        <div className="flex whitespace-nowrap animate-[marquee_30s_linear_infinite] items-center">
          {TICKER_ITEMS.concat(TICKER_ITEMS).map((item, i) => (
            <div key={i} className={`flex items-center text-sm font-mono uppercase ${isLightMode ? "text-[#4B4B55]" : "text-white/40"}`}>
              <span className="mx-6">·</span>
              {item}
            </div>
          ))}
        </div>
      </section>

      {/* Four Pillar Cards */}
      <section id="features" className="py-24 px-6 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Pillar 1 */}
          <div className={`border p-8 rounded-xl transition-colors ${isLightMode ? "bg-[#FFFFFF] border-[#E8E0D8] text-[#1A1A1C] hover:shadow-sm" : "bg-[#111116] border-white/10 hover:border-[#0D9488]/50"}`}>
            <div className={`${isLightMode ? "text-[#1A1A1C]" : "text-[#0D9488]"} mb-6 flex items-center gap-3`}>
              <Database className="w-8 h-8" />
              <span className="font-serif font-bold text-4xl">8</span>
              <span className="text-sm uppercase tracking-widest opacity-80">Antigen Systems</span>
            </div>
            <h3 className="text-2xl font-serif font-bold mb-4">PILLAR 01 — Smart Matching</h3>
            <ul className={`space-y-3 font-light text-sm ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>
              <li className="flex gap-2"><span>•</span> 8-antigen ISBT compatibility scoring</li>
              <li className="flex gap-2"><span>•</span> Neo4j graph-based chain generation</li>
              <li className="flex gap-2"><span>•</span> XGBoost-powered urgency prediction</li>
              <li className="flex gap-2"><span>•</span> Gemini conflict resolver for edge cases</li>
              <li className="flex gap-2"><span>•</span> Automated e-RaktKosh fallback routing</li>
              <li className="flex gap-2"><span>•</span> Historical antibody sensitization checks</li>
              <li className="flex gap-2"><span>•</span> Real-time eligibility gating</li>
            </ul>
          </div>

          {/* Pillar 2 */}
          <div className={`border p-8 rounded-xl transition-colors ${isLightMode ? "bg-[#FFFFFF] border-[#E8E0D8] text-[#1A1A1C] hover:shadow-sm" : "bg-[#111116] border-white/10 hover:border-[#EF4444]/50"}`}>
            <div className={`${isLightMode ? "text-[#C8102E]" : "text-[#EF4444]"} mb-6 flex items-center gap-3`}>
              <Cpu className="w-8 h-8" />
              <span className="font-serif font-bold text-4xl">14</span>
              <span className="text-sm uppercase tracking-widest opacity-80">Autonomous Agents</span>
            </div>
            <h3 className="text-2xl font-serif font-bold mb-4">PILLAR 02 — Care Coordination</h3>
            <ul className={`space-y-3 font-light text-sm ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>
              <li className="flex gap-2"><span>•</span> LangGraph StateGraph orchestration</li>
              <li className="flex gap-2"><span>•</span> Auto-repairing broken donation chains</li>
              <li className="flex gap-2"><span>•</span> AI Voice Calls via Twilio integration</li>
              <li className="flex gap-2"><span>•</span> Natural Language Understanding for intents</li>
              <li className="flex gap-2"><span>•</span> APScheduler for follow-ups and nudges</li>
              <li className="flex gap-2"><span>•</span> WebSocket real-time OC synchronization</li>
              <li className="flex gap-2"><span>•</span> ntfy.sh instant mobile push alerts</li>
            </ul>
          </div>

          {/* Pillar 3 */}
          <div className={`border p-8 rounded-xl transition-colors ${isLightMode ? "bg-[#FFFFFF] border-[#E8E0D8] text-[#1A1A1C] hover:shadow-sm" : "bg-[#111116] border-white/10 hover:border-[#10B981]/50"}`}>
            <div className={`${isLightMode ? "text-[#1A1A1C]" : "text-[#10B981]"} mb-6 flex items-center gap-3`}>
              <Users className="w-8 h-8" />
              <span className="font-serif font-bold text-4xl">40→85%</span>
              <span className="text-sm uppercase tracking-widest opacity-80">Active Donor Rate</span>
            </div>
            <h3 className="text-2xl font-serif font-bold mb-4">PILLAR 03 — Engagement & Continuity</h3>
            <ul className={`space-y-3 font-light text-sm ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>
              <li className="flex gap-2"><span>•</span> XGBoost predictive donor churn modeling</li>
              <li className="flex gap-2"><span>•</span> Automated churn-tier intervention paths</li>
              <li className="flex gap-2"><span>•</span> SVD collaborative filtering for campaigns</li>
              <li className="flex gap-2"><span>•</span> Milestone and emergency hero badge system</li>
              <li className="flex gap-2"><span>•</span> Localized patient impact stories generation</li>
              <li className="flex gap-2"><span>•</span> Persistent `donor_memory` across interactions</li>
              <li className="flex gap-2"><span>•</span> City-wide gamified donation leaderboards</li>
            </ul>
          </div>

          {/* Pillar 4 */}
          <div className={`border p-8 rounded-xl transition-colors ${isLightMode ? "bg-[#FFFFFF] border-[#E8E0D8] text-[#1A1A1C] hover:shadow-sm" : "bg-[#111116] border-white/10 hover:border-[#F59E0B]/50"}`}>
            <div className={`${isLightMode ? "text-[#1A1A1C]" : "text-[#F59E0B]"} mb-6 flex items-center gap-3`}>
              <Globe className="w-8 h-8" />
              <span className="font-serif font-bold text-4xl">10+</span>
              <span className="text-sm uppercase tracking-widest opacity-80">Indian Languages</span>
            </div>
            <h3 className="text-2xl font-serif font-bold mb-4">PILLAR 04 — Operating at Scale</h3>
            <ul className={`space-y-3 font-light text-sm ${isLightMode ? "text-[#4B4B55]" : "text-white/60"}`}>
              <li className="flex gap-2"><span>•</span> WhatsApp & Telegram native interfaces</li>
              <li className="flex gap-2"><span>•</span> Automated langdetect for regional parsing</li>
              <li className="flex gap-2"><span>•</span> Tesseract OCR for report ingestion</li>
              <li className="flex gap-2"><span>•</span> ₹0 cost via open source & free tier stiching</li>
              <li className="flex gap-2"><span>•</span> 1M+ synthetic patient profiles for testing</li>
              <li className="flex gap-2"><span>•</span> Geospatial routing across hospital nodes</li>
              <li className="flex gap-2"><span>•</span> High-availability Render.com backend</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Data Flow Architecture */}
      <section id="architecture" className={`py-24 px-6 border-y overflow-hidden transition-colors ${isLightMode ? "bg-[#F0EAE2] border-[#E8E0D8]" : "bg-[#111116] border-white/10"}`}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-serif font-bold text-4xl mb-4">Data Flow Architecture</h2>
            <p className={isLightMode ? "text-[#6B6572]" : "text-white/50"}>End-to-end pipeline from distress signal to confirmed transfusion.</p>
          </div>
          
          <div className="space-y-8 relative">
            <div className={`absolute left-[50%] top-0 bottom-0 w-px ${isLightMode ? "bg-[#E8E0D8]" : "bg-white/10"}`} />

            <div className="flex items-center justify-center gap-8 relative z-10">
              <div className={`px-6 py-3 border rounded-full text-sm font-mono font-bold ${isLightMode ? "bg-white border-[#C8102E]/30 text-[#C8102E]" : "bg-[#0A0A0C] border-[#C8102E]/30 text-[#C8102E]"}`}>1. Intake (Telegram/Web)</div>
            </div>
            <div className="flex items-center justify-center gap-8 relative z-10">
              <div className={`w-8 h-8 flex items-center justify-center border rounded-full ${isLightMode ? "bg-white border-[#E8E0D8] text-[#1A1A1C]" : "bg-[#111116] border-white/20 text-white"}`}><ArrowRight className="w-4 h-4 rotate-90" /></div>
            </div>
            <div className="flex items-center justify-center gap-8 relative z-10">
              <div className={`px-6 py-3 border rounded-full text-sm font-mono font-bold ${isLightMode ? "bg-white border-[#0D9488]/30 text-[#0D9488]" : "bg-[#0A0A0C] border-[#0D9488]/30 text-[#0D9488]"}`}>2. Neo4j Graph Matching</div>
              <div className={`px-6 py-3 border rounded-full text-sm font-mono font-bold ${isLightMode ? "bg-white border-[#0D9488]/30 text-[#0D9488]" : "bg-[#0A0A0C] border-[#0D9488]/30 text-[#0D9488]"}`}>3. XGBoost Scoring</div>
            </div>
            <div className="flex items-center justify-center gap-8 relative z-10">
              <div className={`w-8 h-8 flex items-center justify-center border rounded-full ${isLightMode ? "bg-white border-[#E8E0D8] text-[#1A1A1C]" : "bg-[#111116] border-white/20 text-white"}`}><ArrowRight className="w-4 h-4 rotate-90" /></div>
            </div>
            <div className="flex items-center justify-center gap-8 relative z-10">
              <div className={`px-6 py-3 border rounded-full text-sm font-mono font-bold ${isLightMode ? "bg-white border-[#10B981]/30 text-[#10B981]" : "bg-[#0A0A0C] border-[#10B981]/30 text-[#10B981]"}`}>4. LangGraph Planner</div>
            </div>
            <div className="flex items-center justify-center gap-8 relative z-10">
              <div className={`w-8 h-8 flex items-center justify-center border rounded-full ${isLightMode ? "bg-white border-[#E8E0D8] text-[#1A1A1C]" : "bg-[#111116] border-white/20 text-white"}`}><ArrowRight className="w-4 h-4 rotate-90" /></div>
            </div>
            <div className="flex items-center justify-center gap-8 relative z-10">
              <div className={`px-6 py-3 border rounded-full text-sm font-mono font-bold ${isLightMode ? "bg-white border-[#F59E0B]/30 text-[#F59E0B]" : "bg-[#0A0A0C] border-[#F59E0B]/30 text-[#F59E0B]"}`}>5. Twilio Voice</div>
              <div className={`px-6 py-3 border rounded-full text-sm font-mono font-bold ${isLightMode ? "bg-white border-[#F59E0B]/30 text-[#F59E0B]" : "bg-[#0A0A0C] border-[#F59E0B]/30 text-[#F59E0B]"}`}>6. Telegram Outreach</div>
            </div>
          </div>
        </div>
      </section>

      {/* System Architecture */}
      <section id="system-arch" className="py-24 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <div className="text-xs font-bold tracking-widest uppercase mb-2 opacity-60">System Architecture</div>
          <h2 className="font-serif font-bold text-4xl mb-4">How it's built</h2>
        </div>
        
        <div className="flex w-full max-w-5xl mx-auto relative">
          {/* Side labels */}
          <div className="hidden md:flex flex-col justify-between py-12 pr-8 border-r border-dashed w-48 text-right font-bold text-[10px] tracking-widest uppercase opacity-70">
            <div className="text-teal-600 dark:text-teal-400">Presentation Layer</div>
            <div className="text-red-600 dark:text-red-400">Intelligence Layer</div>
            <div className="text-amber-600 dark:text-amber-400">Data Layer</div>
          </div>
          
          <div className="flex-1 md:pl-12 space-y-12">
            {/* Tier 1: Frontend */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <LayoutDashboard className="w-7 h-7 text-teal-500" />
                <div>
                  <h4 className="font-medium text-sm">Web Dashboard</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>React + Vite + Tailwind</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-teal-500/10 text-teal-600 dark:text-teal-400 text-[10px] px-2 py-0.5 font-mono">React 18</span>
                </div>
              </div>
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <Smartphone className="w-7 h-7 text-teal-500" />
                <div>
                  <h4 className="font-medium text-sm">Donor Portal</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>Mobile-First PWA</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-teal-500/10 text-teal-600 dark:text-teal-400 text-[10px] px-2 py-0.5 font-mono">PWA</span>
                </div>
              </div>
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <HeartPulse className="w-7 h-7 text-teal-500" />
                <div>
                  <h4 className="font-medium text-sm">Patient Portal</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>Secure Care View</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-teal-500/10 text-teal-600 dark:text-teal-400 text-[10px] px-2 py-0.5 font-mono">Secure</span>
                </div>
              </div>
            </div>
            
            {/* Arrow down */}
            <div className="flex justify-center -my-6 relative z-10">
              <div className={`w-px h-8 ${isLightMode ? "bg-[#E8E0D8]" : "bg-white/20"}`} />
              <div className={`absolute bottom-[-4px] text-[10px] ${isLightMode ? "text-[#E8E0D8]" : "text-white/20"}`}>▼</div>
            </div>

            {/* Tier 2: AI Brain */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <GitBranch className="w-7 h-7 text-[#C8102E]" />
                <div>
                  <h4 className="font-medium text-sm">LangGraph Engine</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>14 Autonomous Agents</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] px-2 py-0.5 font-mono">LangChain</span>
                </div>
              </div>
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <Cpu className="w-7 h-7 text-[#C8102E]" />
                <div>
                  <h4 className="font-medium text-sm">Groq + Gemini</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>Inference · Resolution</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] px-2 py-0.5 font-mono">LLMs</span>
                </div>
              </div>
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <Target className="w-7 h-7 text-[#C8102E]" />
                <div>
                  <h4 className="font-medium text-sm">Matching Engine</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>XGBoost + 8-Antigen</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] px-2 py-0.5 font-mono">ML</span>
                </div>
              </div>
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <Megaphone className="w-7 h-7 text-[#C8102E]" />
                <div>
                  <h4 className="font-medium text-sm">Outreach Layer</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>Telegram · Voice · ntfy</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] px-2 py-0.5 font-mono">Comms</span>
                </div>
              </div>
            </div>

            {/* Arrow down */}
            <div className="flex justify-center -my-6 relative z-10">
              <div className={`w-px h-8 ${isLightMode ? "bg-[#E8E0D8]" : "bg-white/20"}`} />
              <div className={`absolute bottom-[-4px] text-[10px] ${isLightMode ? "text-[#E8E0D8]" : "text-white/20"}`}>▼</div>
            </div>

            {/* Tier 3: Data Layer */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <Database className="w-7 h-7 text-amber-500" />
                <div>
                  <h4 className="font-medium text-sm">Neo4j Aura</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>Graph · 8-hop chains</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[10px] px-2 py-0.5 font-mono">Graph DB</span>
                </div>
              </div>
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <Table2 className="w-7 h-7 text-amber-500" />
                <div>
                  <h4 className="font-medium text-sm">Supabase</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>Profiles · History</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[10px] px-2 py-0.5 font-mono">Relational</span>
                </div>
              </div>
              <div className={`rounded-xl border p-4 flex flex-col gap-3 ${isLightMode ? "bg-white border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
                <Globe className="w-7 h-7 text-amber-500" />
                <div>
                  <h4 className="font-medium text-sm">e-RaktKosh API</h4>
                  <p className={`text-xs ${isLightMode ? "text-[#6B6572]" : "text-slate-400"}`}>National Network</p>
                </div>
                <div className="mt-auto">
                  <span className="rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[10px] px-2 py-0.5 font-mono">External API</span>
                </div>
              </div>
            </div>
            
            {/* Bottom Metrics */}
            <div className={`flex flex-wrap justify-between items-center px-8 py-4 rounded-xl border mt-8 ${isLightMode ? "bg-[#F0EAE2] border-[#E8E0D8]" : "bg-white/5 border-white/10"}`}>
              <div className="text-center px-4">
                <div className="font-mono font-bold text-lg mb-1">14 ms</div>
                <div className="text-[10px] uppercase tracking-wider opacity-60">Avg agent decision</div>
              </div>
              <div className={`w-px h-8 ${isLightMode ? "bg-[#E8E0D8]" : "bg-white/10"}`} />
              <div className="text-center px-4">
                <div className="font-mono font-bold text-lg mb-1">₹0</div>
                <div className="text-[10px] uppercase tracking-wider opacity-60">Monthly infra cost</div>
              </div>
              <div className={`w-px h-8 ${isLightMode ? "bg-[#E8E0D8]" : "bg-white/10"}`} />
              <div className="text-center px-4">
                <div className="font-mono font-bold text-lg mb-1">99.7%</div>
                <div className="text-[10px] uppercase tracking-wider opacity-60">System uptime SLA</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Agents Pipeline */}
      <section id="agents" className={`py-24 px-6 border-y transition-colors ${isLightMode ? "bg-[#F0EAE2] border-[#E8E0D8]" : "bg-[#111116] border-white/10"}`}>
        <div className="text-center mb-16">
          <h2 className="font-serif font-bold text-4xl mb-4">The Multi-Agent Swarm</h2>
          <p className={`max-w-2xl mx-auto ${isLightMode ? "text-[#6B6572]" : "text-white/50"}`}>BloodBridge utilizes a specialized LangGraph architecture where agents coordinate autonomously to resolve supply constraints.</p>
        </div>
        <div className="flex flex-wrap justify-center gap-4 max-w-4xl mx-auto">
          {["MatchingAgent", "PlannerAgent", "OutreachAgent", "ChainMonitorAgent", "ChainRepairAgent", "VoiceAgent", "GamificationAgent", "OutcomeAgent"].map(agent => (
            <div key={agent} className={`px-4 py-2 border rounded-[4px] text-sm font-mono transition-colors cursor-default ${isLightMode ? "bg-white border-[#E8E0D8] text-[#1A1A1C] hover:bg-[#F9F5F0]" : "bg-white/5 border-white/10 text-white/80 hover:bg-white/10"}`}>
              {agent}
            </div>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="bg-[#F5F0E8] text-slate-900 py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-serif font-bold text-4xl mb-4">Powered by Open Source & Free Tiers</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <h4 className="font-bold text-lg mb-4 border-b border-slate-300 pb-2">Frontend</h4>
              <div className="flex flex-wrap gap-2">
                {["React 18", "Vite", "TailwindCSS", "Framer Motion", "ForceGraph2D", "Leaflet", "wouter"].map(t => (
                  <span key={t} className="px-3 py-1 bg-white border border-slate-200 rounded-full text-sm font-medium">{t}</span>
                ))}
              </div>
            </div>
            <div>
              <h4 className="font-bold text-lg mb-4 border-b border-slate-300 pb-2">Backend & AI</h4>
              <div className="flex flex-wrap gap-2">
                {["FastAPI", "LangGraph", "Groq (Llama 3)", "Gemini 1.5 Flash", "XGBoost", "APScheduler"].map(t => (
                  <span key={t} className="px-3 py-1 bg-white border border-slate-200 rounded-full text-sm font-medium">{t}</span>
                ))}
              </div>
            </div>
            <div>
              <h4 className="font-bold text-lg mb-4 border-b border-slate-300 pb-2">Data & Infra</h4>
              <div className="flex flex-wrap gap-2">
                {["Neo4j Aura", "Supabase", "Telegram API", "Twilio", "ntfy.sh", "Render"].map(t => (
                  <span key={t} className="px-3 py-1 bg-white border border-slate-200 rounded-full text-sm font-medium">{t}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className={`py-24 px-6 text-center transition-colors duration-500 ${isLightMode ? "bg-[#F9F5F0]" : "bg-[#0A0A0C]"}`}>
        <h2 className="font-serif text-4xl font-bold mb-8">Ready to see it in action?</h2>
        <Link href="/dashboard/emergency" className="inline-flex bg-[#C8102E] text-white px-8 py-4 rounded-[4px] font-medium text-lg items-center gap-2 hover:bg-[#A00D24] transition-colors mb-12 shadow-md">
          Open Operations Center <ArrowRight className="w-5 h-5" />
        </Link>
        <div className={`flex flex-wrap justify-center gap-6 text-sm font-mono ${isLightMode ? "text-[#6B6572]" : "text-white/40"}`}>
          <span>{`{ status: "online" }`}</span>
          <span>{`{ mock_data: true }`}</span>
          <span>{`{ license: "MIT" }`}</span>
        </div>
      </section>
    </div>
  );
}