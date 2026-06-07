import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ChevronRight, Calendar, Footprints, Mountain, MapPin, Compass, Backpack } from 'lucide-react';

const CaminoIndexPage: React.FC = () => {
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

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-1 bg-stone-200 z-50">
        <div
          className="h-full bg-gradient-to-r from-amber-500 to-orange-600 transition-all duration-300"
          style={{ width: `${scrollProgress}%` }}
        />
      </div>

      {/* Hero Section */}
      <div className="relative h-screen w-full overflow-hidden">
        {/* Background Image with Parallax Effect */}
        <div
          className="absolute inset-0 bg-cover bg-center transform scale-110"
          style={{
            backgroundImage: `url(/camino/image9.jpeg)`,
            transform: `translateY(${scrollProgress * 0.5}px)`
          }}
        />

        {/* Gradient Overlays */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black/80" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

        {/* Navigation */}
        <div className="absolute top-0 left-0 right-0 z-20 p-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-white/90 hover:text-white transition-all bg-white/10 backdrop-blur-md px-5 py-3 rounded-full hover:bg-white/20 border border-white/20"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-medium">Back to HomeIQ</span>
          </Link>
        </div>

        {/* Hero Content */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center px-6 max-w-5xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 rounded-full text-white font-semibold text-sm mb-8 shadow-2xl">
              <Compass className="w-4 h-4" />
              TRAVEL DIARIES
            </div>

            {/* Title */}
            <h1 className="text-7xl md:text-9xl font-black text-white mb-6 tracking-tight leading-none">
              Camino de
              <br />
              <span className="bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
                Santiago
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-2xl md:text-3xl text-white/90 font-light mb-12 max-w-3xl mx-auto leading-relaxed">
              Personal accounts of walking the ancient pilgrimage routes across France and Spain
            </p>

            {/* CTA */}
            <button
              onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
              className="group inline-flex items-center gap-3 bg-white text-stone-900 px-8 py-4 rounded-full font-semibold text-lg hover:bg-amber-500 hover:text-white transition-all shadow-2xl hover:shadow-amber-500/50"
            >
              Explore Journeys
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

      {/* Journey Selection Tiles */}
      <div className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-5xl md:text-6xl font-black text-stone-900 mb-4">Choose Your Journey</h2>
          <p className="text-xl text-stone-600">Three paths, one ancient pilgrimage</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Tile 1: French Way */}
          <Link
            to="/camino/french-way"
            className="group relative overflow-hidden rounded-3xl shadow-2xl hover:shadow-amber-500/50 transition-all duration-500 hover:scale-105"
          >
            <div className="aspect-[4/3] relative">
              <img
                src="/camino/image9.jpeg"
                alt="The French Way"
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-br from-amber-500/20 to-orange-600/20" />

              <div className="absolute inset-0 p-8 flex flex-col justify-end">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-500 rounded-full text-white font-semibold text-xs mb-4 w-fit">
                  <Mountain className="w-3 h-3" />
                  MARCH-APRIL 2012
                </div>
                <h3 className="text-4xl font-black text-white mb-2">The French Way</h3>
                <p className="text-white/90 text-lg mb-4">Le Puy-en-Velay → Pamplona</p>
                <div className="flex items-center gap-4 text-white/80 text-sm">
                  <span className="flex items-center gap-1">
                    <Footprints className="w-4 h-4" />
                    850km
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    28 days
                  </span>
                </div>
              </div>
            </div>
          </Link>

          {/* Tile 2: Spanish Way */}
          <Link
            to="/camino/spanish-way"
            className="group relative overflow-hidden rounded-3xl shadow-2xl hover:shadow-blue-500/50 transition-all duration-500 hover:scale-105"
          >
            <div className="aspect-[4/3] relative">
              <img
                src="/camino/image1.jpeg"
                alt="The Spanish Way"
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-teal-600/20" />

              <div className="absolute inset-0 p-8 flex flex-col justify-end">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500 rounded-full text-white font-semibold text-xs mb-4 w-fit">
                  <MapPin className="w-3 h-3" />
                  MAY 2015
                </div>
                <h3 className="text-4xl font-black text-white mb-2">The Spanish Way</h3>
                <p className="text-white/90 text-lg mb-4">Irun → Santiago (Camino del Norte)</p>
                <div className="flex items-center gap-4 text-white/80 text-sm">
                  <span className="flex items-center gap-1">
                    <Footprints className="w-4 h-4" />
                    817.5km
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    31 days
                  </span>
                </div>
              </div>
            </div>
          </Link>

          {/* Tile 3: Before You Go */}
          <Link
            to="/camino/before-you-go"
            className="group relative overflow-hidden rounded-3xl shadow-2xl hover:shadow-emerald-500/50 transition-all duration-500 hover:scale-105"
          >
            <div className="aspect-[4/3] relative bg-gradient-to-br from-emerald-500 to-green-600">
              <div className="absolute inset-0 flex items-center justify-center">
                <Backpack className="w-32 h-32 text-white/20" />
              </div>

              <div className="absolute inset-0 p-8 flex flex-col justify-end">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-white font-semibold text-xs mb-4 w-fit">
                  <Compass className="w-3 h-3" />
                  PLANNING GUIDE
                </div>
                <h3 className="text-4xl font-black text-white mb-2">Before You Go</h3>
                <p className="text-white/90 text-lg mb-4">Essential tips for walking the Camino</p>
                <div className="text-white/80 text-sm">
                  Everything you need to know before starting your journey
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-stone-900 text-white py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-stone-400 text-lg">Personal travel diaries</p>
          <p className="text-stone-500 text-sm mt-2">Camino de Santiago journeys</p>
        </div>
      </footer>
    </div>
  );
};

export default CaminoIndexPage;
