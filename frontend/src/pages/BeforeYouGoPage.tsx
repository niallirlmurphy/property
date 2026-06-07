import React, { useState, useEffect } from 'react';
import { ArrowLeft, ChevronRight, Compass, Plane, Signpost, Home, MapPin, Backpack, Mountain } from 'lucide-react';
import { Link } from 'react-router-dom';

const BeforeYouGoPage: React.FC = () => {
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
          className="h-full bg-gradient-to-r from-emerald-500 to-green-600 transition-all duration-300"
          style={{ width: `${scrollProgress}%` }}
        />
      </div>

      {/* Hero Section */}
      <div className="relative h-screen w-full overflow-hidden bg-gradient-to-br from-emerald-600 via-emerald-500 to-green-600">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '40px 40px' }} />
        </div>

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
            {/* Icon */}
            <div className="inline-flex items-center justify-center w-24 h-24 bg-white/20 backdrop-blur-md rounded-3xl mb-8">
              <Backpack className="w-12 h-12 text-white" />
            </div>

            {/* Title */}
            <h1 className="text-7xl md:text-9xl font-black text-white mb-6 tracking-tight leading-none">
              Before You Go
            </h1>

            {/* Subtitle */}
            <p className="text-2xl md:text-3xl text-white/90 font-light mb-12 max-w-3xl mx-auto leading-relaxed">
              Essential planning and preparation for walking the Camino
            </p>

            {/* CTA */}
            <button
              onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
              className="group inline-flex items-center gap-3 bg-white text-emerald-600 px-8 py-4 rounded-full font-semibold text-lg hover:bg-emerald-50 transition-all shadow-2xl"
            >
              Start Planning
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
        <div className="prose prose-xl prose-stone max-w-none text-center">
          <p className="text-2xl leading-relaxed text-stone-700 font-light">
            Whether you're walking the French Way or the Spanish Way, proper preparation makes all the difference.
            Here's everything you need to know before starting your pilgrimage.
          </p>
        </div>
      </div>

      {/* Content Sections */}
      <div className="max-w-5xl mx-auto px-6 pb-24 space-y-12">

        {/* Section 1: Pilgrim Passport */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <Compass className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">Pilgrim Passport</h2>
              <div className="prose prose-stone max-w-none">
                <p>Get your pilgrim passport from the Irish Office of the Confraternity of St. James. This will be stamped at each overnight location. Hostels check that you're a genuine pilgrim.</p>

                <p className="font-semibold text-emerald-600 mt-4">Requirements for Santiago Certificate:</p>
                <ul>
                  <li>Minimum last 100km walked (200km for cyclists)</li>
                  <li>Stamps from each stop along your journey</li>
                </ul>

                <p className="font-semibold text-emerald-600 mt-6">The Three Irish Stamps:</p>
                <ol>
                  <li><strong>St. James's Gate</strong> - Guinness tour receptionist will stamp it</li>
                  <li><strong>Local church</strong> - Get a stamp from your parish</li>
                  <li><strong>Hedigan's Brian Boru pub</strong> - Glasnevin, Dublin</li>
                </ol>

                <p className="text-sm text-stone-600 mt-4">Ready for your journey with the blessings of St. James and Brian Boru!</p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Fall Back Plans */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <Plane className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">Fall Back Plans</h2>
              <div className="prose prose-stone max-w-none">
                <p>If you need to end your journey early, there are good transport options:</p>

                <div className="bg-emerald-50 rounded-2xl p-6 mt-4">
                  <p className="font-semibold text-emerald-900 mb-2">Airports with flights to Ireland:</p>
                  <ul className="mb-0">
                    <li>Biarritz</li>
                    <li>Bilbao</li>
                    <li>Santander</li>
                    <li>Santiago</li>
                  </ul>
                </div>

                <p className="mt-4">Good train and bus services connect to all these airports.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Following the Signs */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <Signpost className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">Following the Signs</h2>
              <div className="prose prose-stone max-w-none">
                <p className="font-semibold text-emerald-600">Shell sign with converging lines:</p>
                <ul>
                  <li><strong>In Galicia:</strong> Follow the direction where lines <em>diverge</em> (to the right)</li>
                  <li><strong>Rest of Spain:</strong> Follow the direction where lines <em>converge</em> (to the left)</li>
                </ul>

                <p className="font-semibold text-emerald-600 mt-4">Yellow arrows:</p>
                <p>Most common sign - painted on walls everywhere. Not always as clear as you'd hope!</p>

                <div className="bg-amber-50 border-l-4 border-amber-500 p-4 mt-4">
                  <p className="font-semibold text-amber-900 mb-2">If you miss a turn:</p>
                  <p className="mb-0">Two consecutive junctions with no signs means you missed something. Go back and look for the sign you missed while you were dreaming!</p>
                </div>

                <p className="text-sm text-stone-600 mt-4">Sometimes signs contradict each other - follow the yellow arrow.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Types of Accommodation */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <Home className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">Types of Accommodation</h2>
              <div className="prose prose-stone max-w-none">
                <p><strong>Albergue:</strong> Hostel in Spain</p>
                <p><strong>Hostal:</strong> Unclassified cheap hotel (NOT a hostel!)</p>

                <p className="font-semibold text-emerald-600 mt-6">Three types of hostels:</p>
                <ol>
                  <li><strong>Local council</strong> - Municipal hostels</li>
                  <li><strong>Religious</strong> - Run by volunteers (beautiful human beings)</li>
                  <li><strong>Private</strong> - Most responsive, open all the time, provide food/drink</li>
                </ol>

                <div className="bg-emerald-50 rounded-2xl p-6 mt-6">
                  <p className="font-semibold text-emerald-900 mb-2">Donation-based hostels:</p>
                  <p className="mb-2">Have change ready! Bring 5 or 10 euro notes, not 20s. No change given.</p>
                  <p className="text-sm text-emerald-700 mb-0">Lesson learned: I put in a 20 euro note expecting change. It never came!</p>
                </div>

                <p className="font-semibold text-emerald-600 mt-6">Strategy:</p>
                <ul>
                  <li><strong>General rule:</strong> No pre-booking hostels in Spain</li>
                  <li><strong>Exception:</strong> Pre-book in major cities like San Sebastian</li>
                  <li>Stay in hostels 50%+ of time to meet people and build a core group</li>
                  <li>Try a Rural Casa (country house) at least once - beautiful, European-funded</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Section 5: Getting to Irun */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <MapPin className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">Getting to Irun (from Ireland)</h2>
              <div className="prose prose-stone max-w-none">
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 font-bold text-sm">1</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Flight: Ryanair Dublin → Biarritz</p>
                      <p className="text-sm text-stone-600 mb-0">Regular flights available</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 font-bold text-sm">2</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Bus 816: Biarritz airport → Hendaye</p>
                      <ul className="text-sm mb-0">
                        <li>€2, approximately 1 hour</li>
                        <li>Get timetable from information desk</li>
                        <li>Exit airport, turn left, stop 10 yards up</li>
                        <li>Must flag down the bus</li>
                        <li>Get off at Gare de Hendaye (train station)</li>
                      </ul>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 font-bold text-sm">3</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Eusko Tren: Hendaye → Irun</p>
                      <ul className="text-sm mb-0">
                        <li>€1.65, two stops to downtown Irun</li>
                        <li>Small lovely train</li>
                        <li>Station on left of main station</li>
                        <li>Goes west to Bilbao (less than €10)</li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-stone-50 rounded-2xl p-4 mt-4">
                    <p className="font-semibold text-stone-700 mb-1">Taxi alternative:</p>
                    <p className="text-sm text-stone-600 mb-0">Hendaye → Irun: approximately €10</p>
                  </div>

                  <div className="bg-blue-50 rounded-2xl p-4 mt-4">
                    <p className="font-semibold text-blue-900 mb-1">First night accommodation:</p>
                    <p className="text-sm text-blue-700 mb-0">Albergue de Peregrinos, Calle Lucas de Berroa, Irun</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Section 6: When You Arrive in a Town */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <MapPin className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">When You Arrive in a Town</h2>
              <div className="prose prose-stone max-w-none">
                <p className="font-semibold text-emerald-600">Use your Cicerone guide:</p>
                <ul>
                  <li>Tells you how to get to the hostel</li>
                  <li>Hostel in each stage, plus many in between</li>
                </ul>

                <p className="font-semibold text-emerald-600 mt-6">Finding accommodation:</p>
                <ul>
                  <li>Hotels and pensions cluster near main square</li>
                  <li>Ask a publican (bar owner) - they know the local scene</li>
                  <li>Pensions often on 2nd floor - not obvious at ground level</li>
                  <li>May need to press buzzer for reception</li>
                  <li>Ask "¿Qué piso?" (what floor is reception?)</li>
                </ul>

                <div className="bg-emerald-50 rounded-2xl p-6 mt-6">
                  <p className="font-semibold text-emerald-900 mb-2">Tourist office checklist:</p>
                  <ul className="mb-0">
                    <li>Ask for a map</li>
                    <li>Ask them to pencil in the Camino route</li>
                    <li>Ask for Biblioteca (library) location - free internet</li>
                    <li>Note: Libraries closed 2pm-4pm+</li>
                  </ul>
                </div>

                <p className="font-semibold text-emerald-600 mt-6">Language tips:</p>
                <ul>
                  <li>Most locals have no English</li>
                  <li>Use clear Spanish words or gestures</li>
                  <li>Don't speak full English sentences - it won't help!</li>
                </ul>

                <p className="text-sm text-stone-600 mt-4"><em>Tourist offices won't call pensions on your behalf - you need to find places yourself.</em></p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 7: What to Bring */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <Backpack className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">What to Bring - Comprehensive Checklist</h2>
              <div className="prose prose-stone max-w-none">

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-stone-50 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-stone-900 mb-3">Head</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Broad rim hat</li>
                      <li>Sunglasses</li>
                      <li>2 pairs of glasses/specs</li>
                    </ul>
                  </div>

                  <div className="bg-stone-50 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-stone-900 mb-3">Clothing</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>2 non-stick vests</li>
                      <li>3 t-shirts</li>
                      <li>Normal shirt</li>
                      <li>Fleece</li>
                      <li>Rain gear / cape</li>
                      <li>2 light trousers</li>
                      <li>3 underwear</li>
                    </ul>
                  </div>

                  <div className="bg-stone-50 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-stone-900 mb-3">Footwear</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Walking boots</li>
                      <li>Sandals</li>
                      <li>3 pairs non-slip socks</li>
                    </ul>
                  </div>

                  <div className="bg-stone-50 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-stone-900 mb-3">Gear</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Walking pole</li>
                      <li>Half-litre water container</li>
                      <li>Sleeping bag</li>
                      <li>Plastic bags</li>
                      <li>Head torch</li>
                    </ul>
                  </div>

                  <div className="bg-stone-50 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-stone-900 mb-3">Navigation</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Compass</li>
                      <li>Spanish dictionary</li>
                      <li>Cicerone guide book</li>
                      <li>Personal notes (accommodation, flights, fall-back plans)</li>
                    </ul>
                  </div>

                  <div className="bg-stone-50 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-stone-900 mb-3">Technology</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Mobile phone with camera</li>
                      <li>Charger</li>
                      <li>Socket adapter</li>
                      <li>Music downloads</li>
                      <li>Apps</li>
                    </ul>
                  </div>

                  <div className="bg-emerald-50 rounded-2xl p-6 border-2 border-emerald-200">
                    <h3 className="text-lg font-bold text-emerald-900 mb-3">Medical (Reddy's Pharmacy, Mobhi Rd)</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Antibiotic tablets</li>
                      <li>Blister pads</li>
                      <li>Anti-swelling tablets</li>
                      <li>Sun block / sun cream</li>
                      <li>Tube with needle</li>
                      <li>Scissors and thread</li>
                    </ul>
                  </div>

                  <div className="bg-stone-50 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-stone-900 mb-3">Toiletries & Tools</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Razor</li>
                      <li>Shampoo</li>
                      <li>Pen knife</li>
                      <li>Safety pins</li>
                    </ul>
                  </div>

                  <div className="bg-blue-50 rounded-2xl p-6 border-2 border-blue-200">
                    <h3 className="text-lg font-bold text-blue-900 mb-3">Essential Documents</h3>
                    <ul className="text-sm space-y-1 mb-0">
                      <li>Pilgrim passport</li>
                      <li>Pen (for stamps)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Section 8: Key Differences */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-white">
              <Mountain className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-black text-stone-900 mb-4">Key Differences: Northern vs French Route</h2>
              <div className="prose prose-stone max-w-none">

                <div className="bg-amber-50 border-l-4 border-amber-500 p-6 mb-6">
                  <p className="font-semibold text-amber-900 mb-2">The Northern route is tougher!</p>
                  <p className="mb-0">You will get away with a bit of training in the French Camino but up North you need to have trained very hard.</p>
                </div>

                <div className="grid gap-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 text-2xl">🏔️</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Scenery</p>
                      <p className="text-sm text-stone-600 mb-0">Spectacular - exceeds expectations. Beautiful mountains and valleys everywhere.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 text-2xl">⛰️</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Climbs</p>
                      <p className="text-sm text-stone-600 mb-0">Non-stop tough climbs and tough descents. The price for those beautiful views!</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 text-2xl">💪</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Training Required</p>
                      <p className="text-sm text-stone-600 mb-0">ESSENTIAL. French route is more forgiving, but the Northern route demands serious preparation.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 text-2xl">👥</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">People</p>
                      <p className="text-sm text-stone-600 mb-0">Fewer walkers. May go days without meeting English speakers.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 text-2xl">🌲</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Wilderness</p>
                      <p className="text-sm text-stone-600 mb-0">Absolute wilderness especially week one. If you take a wrong turn, there may be no houses to check with.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 text-2xl">🏠</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Social Strategy</p>
                      <p className="text-sm text-stone-600 mb-0">Stay in hostels 50%+ of the time to meet a core group of people. The company makes the journey.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 text-2xl">🐚</div>
                    <div>
                      <p className="font-semibold text-stone-900 mb-1">Shell Signs</p>
                      <p className="text-sm text-stone-600 mb-0">Interpreted differently in Galicia vs rest of Spain - see "Following the Signs" section above.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Section 9: In Summary */}
        <div className="bg-gradient-to-br from-emerald-600 to-green-600 rounded-3xl p-8 md:p-12 shadow-2xl">
          <div className="text-white">
            <h2 className="text-4xl font-black mb-6">In Summary</h2>
            <div className="prose prose-lg prose-invert max-w-none">
              <p className="text-xl leading-relaxed">
                "The scenery in the Northern route is spectacular exceeding my expectations but these beautiful mountains and valleys everywhere have a price ie there are non stop tough climbs and tough descents."
              </p>
              <p className="text-xl leading-relaxed">
                "You will get away with a bit of training in the French Camino but up North you need to have trained very hard."
              </p>
              <p className="text-emerald-100 font-semibold mt-6">
                Prepare well, train hard, and enjoy the journey. Buen Camino!
              </p>
            </div>
          </div>
        </div>

      </div>

      {/* Footer */}
      <footer className="bg-stone-900 text-white py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-stone-400 text-lg mb-4">Planning guide for the Camino</p>
          <Link to="/camino" className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-semibold">
            View all journeys
            <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </footer>
    </div>
  );
};

export default BeforeYouGoPage;
