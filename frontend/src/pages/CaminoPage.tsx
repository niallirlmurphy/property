import React, { useState, useEffect } from 'react';
import { MapPin, Calendar, ArrowLeft, ChevronRight, Navigation, Mountain, Footprints, Clock, Coffee, Users, Heart } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DayEntry {
  day: number;
  title: string;
  distance?: string;
  content: string;
  image?: string;
  excerpt?: string;
  mood?: string;
}

const CaminoPage: React.FC = () => {
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
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

  const featuredDays: DayEntry[] = [
    {
      day: 1,
      title: "Le Puy to Saint Private d'Allier",
      distance: "31.5km",
      excerpt: "First steps on the trail. Cathedral at dawn. Joyce's Irish pub in rural France. The adventure begins.",
      mood: "excited",
      content: `Le Puy with its Cathedral. The hostel was perfect, I headed off for 7 mass in the Cathedral — no mass. There were a few Germans present and they were ballistic.

The first 20 km is all uphill from 600 metres to 1100 metres and then you come down rapidly to my first overnight in Saint Private d Allier. I could hear the cuckoo — the donkey was crying out also.

The Gite in the town was beautiful. There were three other walkers, a guy from Nantes in France and a mother and daughter from Quebec. Dinner bed and breakfast was 28 euro. After dinner I excused myself — the truth was there was a pub called Joyce's in the town which needed investigation. It was very nice run by an English guy. I headed home at 10 and there was not a sound anywhere — lights out.`,
      image: "/camino/image5.jpeg"
    },
    {
      day: 2,
      title: "Lost in the Mountains",
      distance: "32km + 12km detour",
      excerpt: "Wrong turns. Endless climbs. 13 hours walking. Finding a bed at 8:30pm by sheer determination.",
      mood: "challenging",
      content: `This day was not a good day. I was very over ambitious on distance given the territory. I made a big bloomer leaving town — I followed the wrong route markers and ended up in a forest about 12 to 14 km from Saugues.

After numerous attempts with locals to understand where I was, I ignored advice and wasted a few deadly hours trying to make it across the mountains but I am beaten every time by either barb wire or the forest too dense.

I concede defeat and walk all the way back to Saugues about 12 km. I arrive in town dangerously late at 8.30 — most places are closed. Last stop I go to central hostel. Nobody in charge. I find every bed called for until I go to the 5th room. There are three beds and one is free so come what may I am claiming this bed. I strip like the hammers of hell, jump into bed and face the wall.

Half an hour later those steps start coming up the stairs and there are mild shouts "Oh la la Le homme" — They are two French women. One comes closer and says something like "le vieux homme" (It's an old man). I let on to be asleep all the time. That day I walked hard for 13 hours with just a 20 minute break.`,
      image: "/camino/image3.jpeg"
    },
    {
      day: 3,
      title: "Johnny Cash & Red Wine",
      distance: "32km",
      excerpt: "Alone in a 14-bed dormitory. Mountains at 1,300m. Johnny Cash on my phone. Dancing with wine.",
      mood: "solitary",
      content: `Got up and very confidently exchanged pleasantries with the girls. We are in dog rough mountain territory all above 1000 metres rising to 1300 metres at one stage with the remnants of the snow still on the ground. The grass is white everywhere. No life in any village — coffee you must be joking.

I book into the first Gite near the middle of the town. I am placed in this enormous room with about 14 beds — as it turned out I was the only occupant. I joined a very nice Hungarian couple Joseph and Annie — about 30ish working in the secretariat in Brussels.

When dinner was over 8.15 I slipped out for a pint — horror everyplace closed. I go back to the woman in the Gite and ask for a half bottle of red wine to bring to my room. She gives me a lovely jug of wine. I go to my room and my two sons have helped me with music downloads to my smart phone so Johnny Cash is selected and after a few glasses of wine I am almost waltzing to the music.`,
      image: "/camino/image7.jpeg"
    },
    {
      day: 7,
      title: "Conques - Medieval Beauty",
      distance: "21km",
      excerpt: "One of France's most beautiful villages. Good Friday procession through cobblestone streets. Black pudding like plastic.",
      mood: "inspired",
      content: `Day not too bad. Conques is one of those absolutely beautiful medieval villages in Lot valley. To enter it I had to descend for ever — a warning for tomorrow morning.

Went to the hostel all doors are open again and this time there are written instructions telling you what to do even to the extent of filling out a booking form and putting it in an envelope with the 14 euro and then putting it in a box.

There is a beautiful Cathedral that I visit. It is Good Friday and they are preparing for a procession through town. I join in. Stephano arrives back in hostel with a bag full of food and cans of beer which he insists on sharing with me. They have this black pudding specialty — it is like chewing plastic. It is Stephano's last night so we exchange phone numbers as he says he will come to Ireland.`,
      image: "/camino/image1.jpeg"
    },
    {
      day: 12,
      title: "Rest in Cahors",
      distance: "39km, then rest",
      excerpt: "Walking 70km in two days catches up. Tea and biscuits from a pilgrim volunteer. A computer! Back to civilization.",
      mood: "relief",
      content: `Up early and walked hard. Met a very nice man from Friesland and walked the last 20 km with him. He was about 70, a retired teacher.

I am going over the beautiful bridge into Cahors and this woman in a kiosk on the other side is shouting at me to come over. She is a volunteer in Cahors to help pilgrims. She gives me tea and biscuits and suggests a gite run by an English lady. I quickly find the Gite up this maze of very narrow streets. The Gite name is Papillion Vert (the green butterfly) run by a charming English lady called Jackie.

The best option is to take out one day rest now in Cahors and give my foot a break. The town has everything going for it and Jackie has a computer for me also. The mountains are beautiful but god you need to be back in civilisation every so often.`,
      image: "/camino/image2.jpeg"
    },
    {
      day: 15,
      title: "Ropes and Singing Hymns",
      distance: "38.5km",
      excerpt: "Ropes to pull yourself up rocks. No reservation like Mary and Joseph. Singing hymns at dinner in a convent.",
      mood: "spiritual",
      content: `I felt the long walk today. Some of the walk was in ferocious scrub territory. No human being anywhere. The climb was so steep at one short length over rocks that ropes were in place to pull yourself up.

I head for the convent on the hill near the Cathedral. It is run by volunteers. This guy in charge asks for name I say John, Mr John. He starts to look at his list of reservations. I say no reservation. He says no reservation and drops the list and looks at me. I felt like saying — no reservation like Mary and Joseph going to Bethlehem.

Dinner time came and there was buckets of soup to start. Later the big man gave out hymn sheets and we sang hymns for a few minutes. I visit the Cathedral which is beautiful and the town is beautiful but I need to conserve the energy so I go to bed early.`,
      image: "/camino/image8.jpeg"
    },
    {
      day: 19,
      title: "Finding My People",
      distance: "36km",
      excerpt: "Three weeks alone. Finally meeting English speakers: Conrad the Doc, Philippe the Basque, Geert from Holland. Buckets of wine and stories.",
      mood: "connected",
      content: `Good days walking. Until now I only meet two people briefly who had English as their first language. It is all about to change. I arrive at this communal hostel. I am placed in this big round room of beds. In the middle of the room there is a big table with three guys drinking wine.

The three at the table give me the nod. I join them. We go to a beautiful local shop and get buckets of fish bread and wine and go back to the gite and have a big big meal. It was a nice night. The three at the table were Philippe from Basque country, Conrad the Doc. from Canada, and Geert from Holland.

They were great company and we had buckets of stories and wine and beer to match. The language was split between French and English. Philippe was 67 but looked 55. Geert had those rambling roguish eyes. He was into music and singing. Conrad was a general medical practitioner in Canada. All health services are free in Canada.`,
    },
    {
      day: 26,
      title: "Into the Storm - Crossing the Pyrenees",
      distance: "24.8km",
      excerpt: "The hardest day. Brutal winds. Snow drifts. Lying on the ground unable to stand. Walking stick snaps in two. But I made it.",
      mood: "triumphant",
      content: `Woke a few times during night to horror of hearing high wind. The street signs are banging. It was very simple: high winds go the low route. I put my head down and said nothing and went in front. As it turned out the vast majority opted for the high route. The wind was fierce.

We reach our first challenge at a curve in the path. About eight of us lie down anywhere that is half comfortable because the power of the wind is too strong. Along comes Conrad the Doc. I am delighted to see him because you can take turns walking in each others slip stream to get some relief from the wind.

It feels impossible at times as you raise your foot and the wind pushes you back and your foot lands in the same place or you stumble sideways. We find the path is closed off because of snow drifts. I end up face down in a snow embankment. I jump up and end up being flung against the embankment. I jump up again and am really rolled around on the embankment. This time I surrender. My walking stick has doubled in two.

Down come three poor guys walking with their bikes. They were holding their bikes sideways using the wheels as brakes. Then suddenly they were hit. All three ended up in an exposed embankment lying on the ground. There was no panic. On the contrary most of us looked on the funny side of it.

In terms of energy drain it certainly was one of the hardest days I endured but I am glad I did it. Quite a few turned back and got taxis.`,
      image: "/camino/image9.jpeg"
    },
    {
      day: 28,
      title: "Pamplona - Journey's End",
      distance: "22km",
      excerpt: "Saying goodbye to Conrad and Philippe. Three weeks of testing solitude followed by two weeks of friendship. The Camino complete.",
      mood: "bittersweet",
      content: `Still wet and muddy but another cake walk so I split with my two friends in Pamplona as they go on. That is the not nice part of the whole thing. I had become good friends with Conrad the Doc. and Philippe the Basque. We understood each other and went our own way at times to be alone but the company was very good and I spent two great weeks with them.

The three weeks prior to that were testing as several days I walked 35 plus km without seeing more than one or two walkers and in all this time when there was company it was invariably with non English speaking or individuals with very little English.

I think the cafe and pub culture in Spain and France is very healthy. The owner of the bar or cafe is quite happy to have two people there for an hour. This morning Sunday the little cafes were full of people having their croissant and coffee. It is a big social occasion.`,
      image: "/camino/image10.jpeg"
    }
  ];

  const moodColors = {
    excited: 'from-green-400 to-emerald-500',
    challenging: 'from-red-400 to-orange-500',
    solitary: 'from-blue-400 to-indigo-500',
    inspired: 'from-purple-400 to-pink-500',
    relief: 'from-teal-400 to-cyan-500',
    spiritual: 'from-amber-400 to-yellow-500',
    connected: 'from-rose-400 to-pink-500',
    triumphant: 'from-orange-500 to-red-600',
    bittersweet: 'from-slate-400 to-gray-500',
  };

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-1 bg-stone-200 z-50">
        <div
          className="h-full bg-gradient-to-r from-amber-500 to-orange-600 transition-all duration-300"
          style={{ width: `${scrollProgress}%` }}
        />
      </div>

      {/* Hero - Immersive Full Screen */}
      <div className="relative h-screen w-full overflow-hidden">
        {/* Background Image with Parallax Effect */}
        <div
          className="absolute inset-0 bg-cover bg-center transform scale-110"
          style={{
            backgroundImage: `url(/camino/image9.jpeg)`,
            transform: `translateY(${scrollProgress * 0.5}px)`
          }}
        />

        {/* Gradient Overlays for Depth */}
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
              <Navigation className="w-4 h-4" />
              TRAVEL DIARY
            </div>

            {/* Title */}
            <h1 className="text-7xl md:text-9xl font-black text-white mb-6 tracking-tight leading-none">
              Walking
              <br />
              <span className="bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
                the Camino
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-2xl md:text-3xl text-white/90 font-light mb-12 max-w-3xl mx-auto leading-relaxed">
              850 kilometers. 28 days. Through the mountains of France and Spain on the ancient pilgrimage route.
            </p>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
              {[
                { icon: <Calendar className="w-5 h-5" />, label: 'March-April', value: '2012' },
                { icon: <Footprints className="w-5 h-5" />, label: 'Distance', value: '850km' },
                { icon: <Mountain className="w-5 h-5" />, label: 'Peak', value: '1,400m' },
                { icon: <Clock className="w-5 h-5" />, label: 'Days', value: '28' },
              ].map((stat, idx) => (
                <div key={idx} className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 hover:bg-white/20 transition-all">
                  <div className="text-amber-400 mb-2">{stat.icon}</div>
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-sm text-white/70">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* CTA */}
            <button
              onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
              className="group inline-flex items-center gap-3 bg-white text-stone-900 px-8 py-4 rounded-full font-semibold text-lg hover:bg-amber-500 hover:text-white transition-all shadow-2xl hover:shadow-amber-500/50"
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
          <p className="text-2xl leading-relaxed text-stone-700 font-light first-letter:text-7xl first-letter:font-bold first-letter:text-amber-600 first-letter:float-left first-letter:mr-3 first-letter:leading-none">
            The walk from Le Puy in France to Pamplona was ambitious — longer daily distances than recommended.
            I allowed extra days for bad weather and the unexpected. The route starts in the Massif Central,
            a high barren volcanic region, descends into the lovely Lot valley, crosses the Midi Pyrenees,
            then over the Pyrenees and west to Pamplona.
          </p>
        </div>
      </div>

      {/* Route Map */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          <div className="p-8 md:p-12">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center text-white">
                <MapPin className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-3xl md:text-4xl font-black text-stone-900">The Route</h2>
                <p className="text-stone-600">Le Puy-en-Velay, France → Pamplona, Spain</p>
              </div>
            </div>

            {/* Map Container with Route */}
            <div className="relative rounded-2xl overflow-hidden bg-stone-100" style={{ height: '600px' }}>
              <iframe
                src="https://www.openstreetmap.org/export/embed.html?bbox=0.8%2C42.7%2C3.9%2C45.2&layer=mapnik"
                width="100%"
                height="100%"
                style={{ border: 'none' }}
                title="Camino Route from Le Puy to Pamplona"
              />

              {/* Route Overlay Description */}
              <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-2xl p-4 shadow-lg max-w-sm">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-1 bg-gradient-to-r from-amber-500 to-orange-600 rounded-full" />
                  <span className="text-xs font-bold text-stone-700 uppercase tracking-wide">The Route</span>
                </div>
                <p className="text-xs text-stone-600 leading-relaxed">
                  The <strong>GR 65 / Camino de Santiago</strong> from Le Puy-en-Velay through the Massif Central,
                  Lot Valley, and Pyrenees to Pamplona. Part of the UNESCO World Heritage pilgrimage route.
                </p>
              </div>

              {/* Interactive Waypoints */}
              <div className="absolute bottom-4 left-4 right-4 bg-white/95 backdrop-blur-sm rounded-2xl p-4 shadow-lg">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  {[
                    { name: 'Le Puy', emoji: '🏔️', desc: 'Start - 629m' },
                    { name: 'Conques', emoji: '⛪', desc: 'Medieval village' },
                    { name: 'Cahors', emoji: '🌉', desc: 'Rest day' },
                    { name: 'Moissac', emoji: '🏛️', desc: 'Abbey' },
                    { name: 'Pyrenees', emoji: '⛰️', desc: 'Peak - 1,400m' },
                    { name: 'St-Jean', emoji: '🇫🇷', desc: 'Last stop France' },
                    { name: 'Roncesvalles', emoji: '🇪🇸', desc: 'First stop Spain' },
                    { name: 'Pamplona', emoji: '🎯', desc: 'End - 449m' },
                  ].map((point, idx) => (
                    <div key={idx} className="bg-amber-50 rounded-lg p-2">
                      <div className="text-base mb-0.5">{point.emoji}</div>
                      <div className="font-bold text-stone-900 text-xs">{point.name}</div>
                      <div className="text-stone-500 text-[10px]">{point.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm px-4 py-2 rounded-full text-xs text-stone-700">
                <a
                  href="https://umap.openstreetmap.fr/en/map/chemin-de-saint-jacques-de-compostelle_73436#7/43.5/1.5"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-amber-600 transition-colors font-medium"
                >
                  View Full Route Map →
                </a>
              </div>
            </div>

            {/* Route Highlights */}
            <div className="grid md:grid-cols-3 gap-6 mt-8">
              <div className="bg-amber-50 rounded-2xl p-6">
                <div className="text-amber-600 font-bold mb-2 text-sm uppercase tracking-wide">Start</div>
                <div className="text-xl font-bold text-stone-900">Le Puy-en-Velay</div>
                <div className="text-stone-600 text-sm">Auvergne, France</div>
                <div className="text-stone-500 text-xs mt-2">Elevation: 629m</div>
              </div>

              <div className="bg-orange-50 rounded-2xl p-6">
                <div className="text-orange-600 font-bold mb-2 text-sm uppercase tracking-wide">Highest Point</div>
                <div className="text-xl font-bold text-stone-900">Col de Somport</div>
                <div className="text-stone-600 text-sm">Pyrenees</div>
                <div className="text-stone-500 text-xs mt-2">Elevation: 1,400m</div>
              </div>

              <div className="bg-red-50 rounded-2xl p-6">
                <div className="text-red-600 font-bold mb-2 text-sm uppercase tracking-wide">End</div>
                <div className="text-xl font-bold text-stone-900">Pamplona</div>
                <div className="text-stone-600 text-sm">Navarre, Spain</div>
                <div className="text-stone-500 text-xs mt-2">Elevation: 449m</div>
              </div>
            </div>

            {/* Visual Route Timeline */}
            <div className="mt-8 pt-8 border-t-2 border-stone-100">
              <h3 className="text-xl font-bold text-stone-900 mb-6">The 850km Journey</h3>

              {/* Route Flow */}
              <div className="relative">
                {/* Connecting Line */}
                <div className="absolute top-6 left-6 right-6 h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-red-600 rounded-full" />

                {/* Stops */}
                <div className="relative grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { name: 'Le Puy-en-Velay', region: 'Massif Central', km: '0' },
                    { name: 'Saint-Privat-d\'Allier', region: 'Auvergne', km: '32' },
                    { name: 'Saugues', region: 'Mountains', km: '64' },
                    { name: 'Conques', region: 'Lot Valley', km: '170' },
                    { name: 'Cahors', region: 'Rest Day', km: '340' },
                    { name: 'Moissac', region: 'Midi-Pyrénées', km: '500' },
                    { name: 'Saint-Jean-Pied-de-Port', region: 'Basque Country', km: '750' },
                    { name: 'Pamplona', region: 'Navarre', km: '850' },
                  ].map((stop, idx) => (
                    <div key={idx} className="relative">
                      {/* Marker */}
                      <div className="relative z-10 w-12 h-12 rounded-full bg-white border-4 border-amber-500 mx-auto mb-3 flex items-center justify-center shadow-lg">
                        <span className="text-xs font-bold text-amber-600">{idx + 1}</span>
                      </div>
                      {/* Info */}
                      <div className="text-center">
                        <div className="font-bold text-stone-900 text-sm mb-1">{stop.name}</div>
                        <div className="text-stone-500 text-xs mb-1">{stop.region}</div>
                        <div className="inline-block bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                          {stop.km} km
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Route Stats */}
              <div className="grid md:grid-cols-3 gap-4 mt-8">
                <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-100">
                  <div className="text-amber-600 text-xs font-bold mb-1 uppercase">Stage 1</div>
                  <div className="font-bold text-stone-900">Le Puy → Conques</div>
                  <div className="text-stone-600 text-sm">Massif Central highlands</div>
                </div>
                <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-4 border border-orange-100">
                  <div className="text-orange-600 text-xs font-bold mb-1 uppercase">Stage 2</div>
                  <div className="font-bold text-stone-900">Conques → St-Jean</div>
                  <div className="text-stone-600 text-sm">Lot Valley & Pyrénées</div>
                </div>
                <div className="bg-gradient-to-br from-red-50 to-pink-50 rounded-xl p-4 border border-red-100">
                  <div className="text-red-600 text-xs font-bold mb-1 uppercase">Stage 3</div>
                  <div className="font-bold text-stone-900">St-Jean → Pamplona</div>
                  <div className="text-stone-600 text-sm">Over the Pyrenees</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Featured Stories - Magazine Grid */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h2 className="text-5xl md:text-6xl font-black text-stone-900 mb-4">The Journey</h2>
          <p className="text-xl text-stone-600">28 days of stories, struggles, and serendipity</p>
        </div>

        <div className="space-y-24">
          {featuredDays.map((day, idx) => (
            <article
              key={day.day}
              className={`grid md:grid-cols-2 gap-8 items-center ${
                idx % 2 === 1 ? 'md:grid-flow-dense' : ''
              }`}
            >
              {/* Image */}
              <div
                className={`relative group cursor-pointer ${
                  idx % 2 === 1 ? 'md:col-start-2' : ''
                }`}
                onClick={() => setSelectedDay(selectedDay === day.day ? null : day.day)}
              >
                <div className="relative overflow-hidden rounded-3xl shadow-2xl aspect-[4/3]">
                  <img
                    src={day.image || '/camino/image5.jpeg'}
                    alt={day.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />

                  {/* Day Badge */}
                  <div className="absolute top-6 right-6">
                    <div className={`bg-gradient-to-br ${moodColors[day.mood as keyof typeof moodColors] || 'from-amber-500 to-orange-600'} text-white px-6 py-3 rounded-2xl font-bold text-lg shadow-2xl`}>
                      Day {day.day}
                    </div>
                  </div>

                  {/* Distance Badge */}
                  {day.distance && (
                    <div className="absolute bottom-6 left-6">
                      <div className="bg-white/90 backdrop-blur-sm text-stone-900 px-4 py-2 rounded-full font-semibold text-sm flex items-center gap-2">
                        <Footprints className="w-4 h-4" />
                        {day.distance}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className={idx % 2 === 1 ? 'md:col-start-1 md:row-start-1' : ''}>
                <div className="space-y-4">
                  <h3 className="text-4xl md:text-5xl font-black text-stone-900 leading-tight">
                    {day.title}
                  </h3>

                  <p className="text-xl text-stone-600 leading-relaxed font-light">
                    {day.excerpt}
                  </p>

                  {selectedDay === day.day && (
                    <div className="prose prose-lg prose-stone max-w-none pt-4 border-t-2 border-stone-200">
                      {day.content.split('\n\n').map((paragraph, pIdx) => (
                        <p key={pIdx} className="text-stone-700 leading-relaxed">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={() => setSelectedDay(selectedDay === day.day ? null : day.day)}
                    className="inline-flex items-center gap-2 text-amber-600 hover:text-amber-700 font-semibold group mt-2"
                  >
                    {selectedDay === day.day ? 'Show Less' : 'Read Full Story'}
                    <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>

      {/* Pull Quote */}
      <div className="bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 py-32 my-24">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <div className="text-white/40 text-8xl font-serif mb-4">"</div>
          <blockquote className="text-4xl md:text-5xl font-light text-white leading-tight mb-8">
            The mountains are beautiful but god you need to be back in civilisation every so often.
          </blockquote>
          <p className="text-white/90 text-xl">— Day 12, Rest in Cahors</p>
        </div>
      </div>

      {/* Journey Stats */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { icon: <Coffee className="w-8 h-8" />, number: '28', label: 'Gîtes & Hostels', detail: '€14-€31 per night' },
            { icon: <Users className="w-8 h-8" />, number: '3', label: 'Walking Companions', detail: 'Conrad, Philippe, Geert' },
            { icon: <Heart className="w-8 h-8" />, number: '1', label: "Joyce's Irish Pub", detail: 'In rural France!' },
          ].map((stat, idx) => (
            <div key={idx} className="text-center p-8 bg-white rounded-3xl shadow-xl hover:shadow-2xl transition-shadow">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl text-white mb-4">
                {stat.icon}
              </div>
              <div className="text-5xl font-black text-stone-900 mb-2">{stat.number}</div>
              <div className="text-xl font-semibold text-stone-700 mb-1">{stat.label}</div>
              <div className="text-sm text-stone-500">{stat.detail}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Conclusion */}
      <div className="max-w-4xl mx-auto px-6 py-24">
        <div className="bg-gradient-to-br from-stone-900 to-stone-800 rounded-3xl p-12 md:p-16 text-white shadow-2xl">
          <h2 className="text-4xl md:text-5xl font-black mb-6">The End of the Road</h2>
          <p className="text-xl leading-relaxed mb-6 text-white/90">
            That completes stages 1 and 2 of the trail of St. James from Le Puy in France to Santiago —
            almost 1,000 miles. Stage 2 walked in 2008, Stage 1 in 2012.
          </p>
          <p className="text-2xl font-light text-amber-400">
            It was lovely and thanks to everyone that helped.
          </p>
        </div>
      </div>

      {/* Getting There */}
      <div className="bg-stone-100 py-24">
        <div className="max-w-4xl mx-auto px-6">
          <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl">
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-shrink-0 w-12 h-12 bg-amber-500 rounded-2xl flex items-center justify-center text-white">
                <MapPin className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-3xl font-black text-stone-900 mb-2">
                  Getting Back: Pamplona → Dublin
                </h3>
                <p className="text-stone-600">
                  Bus to Bilbao (€17, 2+ hours), then fly home. Book bus tickets early to avoid sellout.
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mt-8">
              <div className="bg-amber-50 rounded-2xl p-6">
                <h4 className="font-bold text-stone-900 mb-3 text-lg">Weekdays</h4>
                <div className="text-sm text-stone-700 space-y-1">
                  <p>7:00 • 10:00 • 13:00</p>
                  <p>15:30 • 18:00 • 20:30</p>
                </div>
              </div>
              <div className="bg-amber-50 rounded-2xl p-6">
                <h4 className="font-bold text-stone-900 mb-3 text-lg">Weekends</h4>
                <div className="text-sm text-stone-700 space-y-1">
                  <p>9:00 • 11:15 • 16:00</p>
                  <p>17:30 • 20:00</p>
                </div>
              </div>
            </div>

            <p className="text-sm text-stone-500 mt-6">
              Bus: Park Castillo underground station. Bilbao airport bus: €2 vs €25+ taxi.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-stone-900 text-white py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-stone-400 text-lg">A personal travel diary</p>
          <p className="text-stone-500 text-sm mt-2">March - April 2012</p>
        </div>
      </footer>
    </div>
  );
};

export default CaminoPage;
