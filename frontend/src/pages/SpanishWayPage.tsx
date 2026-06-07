import React, { useState, useEffect } from 'react';
import { MapPin, Calendar, ArrowLeft, ChevronRight, Footprints, Coffee, Users, Heart } from 'lucide-react';
import { Link } from 'react-router-dom';

interface StageEntry {
  stage: number;
  title: string;
  route: string;
  distance: string;
  excerpt: string;
  content: string;
  image?: string;
  region: 'basque' | 'cantabria' | 'asturias' | 'galicia';
}

const SpanishWayPage: React.FC = () => {
  const [selectedStage, setSelectedStage] = useState<number | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (window.pageYOffset / totalScroll) * 100;
      setScrollProgress(progress);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const regionColors = {
    basque: 'from-emerald-400 to-green-500',
    cantabria: 'from-blue-400 to-cyan-500',
    asturias: 'from-teal-400 to-cyan-500',
    galicia: 'from-purple-400 to-pink-500',
  };

  // Stages data will be added in the next task
  const stages: StageEntry[] = [];

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-1 bg-stone-200 z-50">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-teal-600 transition-all duration-300"
          style={{ width: `${scrollProgress}%` }}
        />
      </div>

      {/* Hero - Immersive Full Screen */}
      <div className="relative h-screen w-full overflow-hidden">
        {/* Background Image with Parallax Effect */}
        <div
          className="absolute inset-0 bg-cover bg-center transform scale-110"
          style={{
            backgroundImage: `url(/camino/image1.jpeg)`,
            transform: `translateY(${scrollProgress * 0.5}px)`
          }}
        />

        {/* Gradient Overlays for Depth */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black/80" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

        {/* Navigation */}
        <div className="absolute top-0 left-0 right-0 z-20 p-6">
          <Link
            to="/camino"
            className="inline-flex items-center gap-2 text-white/90 hover:text-white transition-all bg-white/10 backdrop-blur-md px-5 py-3 rounded-full hover:bg-white/20 border border-white/20"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-medium">Back to Camino Journeys</span>
          </Link>
        </div>

        {/* Hero Content */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center px-6 max-w-5xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 rounded-full text-white font-semibold text-sm mb-8 shadow-2xl">
              <MapPin className="w-4 h-4" />
              TRAVEL DIARY
            </div>

            {/* Title */}
            <h1 className="text-7xl md:text-9xl font-black text-white mb-6 tracking-tight leading-none">
              Walking
              <br />
              <span className="bg-gradient-to-r from-blue-400 via-teal-500 to-cyan-500 bg-clip-text text-transparent">
                the Spanish Way
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-2xl md:text-3xl text-white/90 font-light mb-12 max-w-3xl mx-auto leading-relaxed">
              817.5 kilometers along Spain's northern coast from Irun to Santiago on the Camino del Norte
            </p>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
              {[
                { icon: <Calendar className="w-5 h-5" />, label: 'May', value: '2015' },
                { icon: <Footprints className="w-5 h-5" />, label: 'Distance', value: '817.5km' },
                { icon: <MapPin className="w-5 h-5" />, label: 'Route', value: 'Coastal' },
                { icon: <Calendar className="w-5 h-5" />, label: 'Days', value: '31' },
              ].map((stat, idx) => (
                <div key={idx} className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 hover:bg-white/20 transition-all">
                  <div className="text-blue-400 mb-2">{stat.icon}</div>
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-sm text-white/70">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* CTA */}
            <button
              onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
              className="group inline-flex items-center gap-3 bg-white text-stone-900 px-8 py-4 rounded-full font-semibold text-lg hover:bg-blue-500 hover:text-white transition-all shadow-2xl hover:shadow-blue-500/50"
            >
              Start Reading
              <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-white/50 rounded-full flex items-start justify-center p-2">
            <div className="w-1 h-2 bg-white rounded-full" />
          </div>
        </div>
      </div>

      {/* Introduction */}
      <div className="max-w-4xl mx-auto px-6 py-24">
        <div className="prose prose-xl prose-stone max-w-none">
          <p className="text-2xl leading-relaxed text-stone-700 font-light first-letter:text-7xl first-letter:font-bold first-letter:text-blue-600 first-letter:float-left first-letter:mr-3 first-letter:leading-none">
            There are all sorts of alternative ways of doing the Camino. The Camino Frances is the starting point for most individuals walking the Camino. The route described here is called the Camino del Norte. It runs from Irun on the border with France to Santiago joining the Camino Frances for the final stage. The route is very scenic and goes along the coast taking in beautiful cities like San Sebastian, Bilbao, Santander. The climbs are tougher than the Camino Frances but as the saying goes "no pain no gain". Enjoy.
          </p>
        </div>
      </div>

      {/* Stages will be rendered here in a future task */}

      {/* Footer */}
      <footer className="bg-stone-900 text-white py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-stone-400 text-lg">A personal travel diary</p>
          <p className="text-stone-500 text-sm mt-2">May 2015</p>
        </div>
      </footer>
    </div>
  );
};

export default SpanishWayPage;
