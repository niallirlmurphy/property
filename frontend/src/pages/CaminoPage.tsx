import React, { useState } from 'react';
import { MapPin, Calendar, ArrowLeft, ChevronDown, Mountain, Footprints, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DayEntry {
  day: number;
  title: string;
  distance?: string;
  content: string;
  image?: string;
  highlight?: string;
}

const CaminoPage: React.FC = () => {
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set([1]));

  const toggleDay = (day: number) => {
    const newExpanded = new Set(expandedDays);
    if (newExpanded.has(day)) {
      newExpanded.delete(day);
    } else {
      newExpanded.add(day);
    }
    setExpandedDays(newExpanded);
  };

  const dayEntries: DayEntry[] = [
    {
      day: 1,
      title: "Le Puy to Saint Private d'Allier",
      distance: "31.5km",
      highlight: "First day on the trail - discovering Joyce's Irish pub in a tiny French village!",
      content: `Le Puy with its Cathedral. Met Seamus's friend last night and had a good chat with him re everything French. The hostel was perfect, I headed off for 7 mass in the Cathedral — no mass. There were a few Germans present and they were ballistic. Headed off. The first 20 km is all uphill from 600 metres to 1100 metres and then you come down rapidly to my first overnight in Saint Private d Allier.

The day went fine one minor error — in France they mark the route going both ways to help walkers walking the opposite direction — a good idea but if you go in a bit of a loop off to see something then when you come back it is very easy to follow the signs in the wrong direction which I did. I met two walkers going the wrong way and then I noticed the sun was in the wrong place so I quickly adjusted.

I could hear the cuckoo — the donkey was crying out also. The Gite in the town was beautiful. There were three other Walkers, a guy from Nantes in France and a mother and daughter from Quebec. Dinner bed and breakfast was 28 euro. The guy from Nantes walked for a few months every year. After dinner at 8ish he was stretching himself getting ready for bed. I excused myself saying I needed a walk after dinner — the truth was there was a pub called Joyces in the town which needed investigation. It was very nice run by an English guy. I headed home at 10 and there was not a sound anywhere — lights out.`,
      image: "/camino/image5.jpeg"
    },
    {
      day: 2,
      title: "Saint Private d'Allier to Saugues",
      distance: "32km",
      highlight: "Lost in the mountains, walking 13 hours straight, claiming a bed at 8:30pm",
      content: `This day was not a good day. I was very over ambitious on distance given the territory. I should have listened to my friend from Nantes as he was a veteran of the route. I did the first half fine even if the climbs were very challenging and was in Saugues for the end of 1200 mass in the Cathedral.

I made a big bloomer leaving town — there is more than one route marked and yes in my over confidence I followed the wrong one out of town — I followed yellow arrows which is the colour of the camino arrows in Spain. I ended up in a forest about 12 to 14 km from Saugues. I find a house and knock on a door and an elderly woman comes out and after numerous attempts we establish where ici (here) is. She says you need to go back to Saugues. I then ignore her advice and waste a few deadly hours trying to make it across the mountains but I am beaten every time by either barb wire or the forest too dense.

I then have a serious chat with myself and head bent I concede defeat and walk all the way back to Saugues about 12 km. I arrive in town and I know I am dangerously late at 8.30 — most places are closed. Last stop I go to central hostel in town. Nobody in charge. I then proceed through the hostel and find every bed called for until I go to the 5th room. There are three beds and one is free so come what may I am claiming this bed. I strip like the hammers of hell, jump into bed and face the wall.

Yes a half an hour later those steps start coming up the stairs and there are mild shouts "Oh la la Le homme" — They are two French women. One comes closer and says something like "le vieux homme" (It's an old man) that seemed to keep them half quiet and I let on to be asleep all the time. That day I walked hard for 13 hours with just a 20 minute break.`,
      image: "/camino/image3.jpeg"
    },
    {
      day: 3,
      title: "Saugues to Saint Alban sur Limagnole",
      distance: "32km",
      highlight: "Johnny Cash and red wine alone in a 14-bed dormitory",
      content: `Got up and very confidently exchanged pleasantries with the girls. I felt half ok and headed off but I improved every half hour. That is not to say it was easy. We are in dog rough mountain territory all above 1000 metres rising to 1300 metres at one stage with the remnants of the snow still on the ground. The grass is white everywhere. No life in any village — coffee you must be joking.

Happy with day but still a half day behind. I book into the first Gite near the middle of the town 31 euro for dinner bed and breakfast. I am placed in this enormous room with about 14 beds — as it turned out I was the only occupant. I noticed there was a pub next door.

I joined a very nice Hungarian couple Joseph and Annie — about 30ish working in the secretariat in Brussels so we had a lot in common and had a great chat. They told me they were on a budget so when the nice lady came to pour the wine I said no thanks. When dinner was over 8.15 I slipped out for a pint — horror everyplace closed. I go back to the woman in the Gite and ask for a half bottle of red wine to bring to my room. She gives me a lovely jug of wine. I go to my room and my two sons have helped me with music downloads to my smart phone so Johnny Cash is selected and after a few glasses of wine I am almost waltzing to the music.`,
      image: "/camino/image7.jpeg"
    },
    {
      day: 7,
      title: "Golinhac to Conques",
      distance: "21km",
      highlight: "One of France's most beautiful medieval villages",
      content: `Day not too bad. Meet up with two new Frenchmen on the route. Conques is one of those absolutely beautiful medieval villages in Lot valley. To enter it I had to descend for ever — a warning for tomorrow morning.

Went to the hostel all doors are open again and this time there are written instructions telling you what to do even to the extent of filling out a booking form and putting it in an envelope with the 14 euro and then putting it in a box. There are three of us only in the hostel: Stephano, the Dutch woman and myself.

There is a beautiful Cathedral that I visit. It is Good Friday and they are preparing for a procession through town. I join in. Stephano arrives back in hostel with a bag full of food and cans of beer which he insists on sharing with me. They have this black pudding specialty — it is like chewing plastic. It is Stephano's last night so we exchange phone numbers as he says he will come to Ireland.`,
      image: "/camino/image1.jpeg"
    },
    {
      day: 12,
      title: "Varaire to Cahors",
      distance: "39km",
      highlight: "Back to civilization - tea, biscuits, and a computer!",
      content: `Up early and walked hard. Met a very nice man from Friesland and walked the last 20 km with him. He was about 70 and was part of the group of 6 that I met way back in Nasbinals. Now my friend from Friesland peeled off as he felt he could do 30/40 km per day like me. He left his wife by agreement with the other group. He is a retired teacher.

I am going over the beautiful bridge into Cahors and this woman in a kiosk on the other side is shouting at me to come over. She is a volunteer in Cahors to help pilgrims. She gives me tea and biscuits and she suggests a gite run by an English lady. I quickly find the Gite up this maze of very narrow streets. The Gite name is Papillion Vert (the green butterfly) run by a charming English lady called Jackie.

I think it will not serve much purpose for me to start dividing one or two of those days. The best option is to take out one day rest now in Cahors and give my foot a break. The town has everything going for it and Jackie has a computer for me also. The mountains are beautiful but god you need to be back in civilisation every so often.`,
      image: "/camino/image2.jpeg"
    },
    {
      day: 15,
      title: "Montcuq to Moissac",
      distance: "38.5km",
      highlight: "Ropes to pull yourself up rocks, arriving at the cathedral",
      content: `I felt the long walk today. Some of the walk was in ferocious scrub territory. No human being anywhere. The climb was so steep at one short length over rocks that ropes were in place to pull yourself up. Then you come to the outskirts of Moissac and you think you are there but like all big cities an hour later I am still walking.

I head for the convent on the hill near the Cathedral. It is run by volunteers which is great but volunteers need to be managed. This guy in charge asks for name I say John, Mr John. He starts to look at his list of reservations. I say no reservation. He says no reservation and drops the list and looks at me. I felt like saying — no reservation like Mary and Joseph going to Bethlehem.

Dinner time came and there was buckets of soup to start. Later the big man gave out hymn sheets and we sang hymns for a few minutes. I visit the Cathedral which is beautiful and the town is beautiful but I need to conserve the energy so I go to bed early.`,
      image: "/camino/image8.jpeg"
    },
    {
      day: 19,
      title: "Montreal du Gers to Nogaro",
      distance: "36km",
      highlight: "Finally meeting English speakers - Conrad the Doc, Philippe the Basque, and Geert from Holland",
      content: `Good days walking. Until now I only meet two people briefly who had English as their first language. It is all about to change. I arrive at this communal hostel. I am placed in this big round room of beds. In the middle of the room there is a big table with three guys drinking wine.

The three at the table give me the nod. I join them. We go to a beautiful local shop and get buckets of fish bread and wine and go back to the gite and have a big big meal. It was a nice night. The three at the table were Philippe from Basque country, Conrad the Doc. from Canada, and Geert from Holland.

They were great company and we had buckets of stories and wine and beer to match. The language was split between French and English. Philippe was 67 but looked 55. Geert had those rambling roguish eyes. He was into music and singing. Philippe was retired from the Department of youth and sport. Conrad was a general medical practitioner in Canada. All health services are free in Canada including your visit to the GP.`,
    },
    {
      day: 26,
      title: "Saint-Jean-Pied-de-Port to Roncesvalles (Spain)",
      distance: "24.8km",
      highlight: "The hardest day - crossing the Pyrenees in brutal wind and snow",
      content: `Woke a few times during night to horror of hearing high wind. We go outside and the street signs are banging and who comes along the street but the man giving advice. It was very simple: high winds go the low route. I put my head down and said nothing and went in front. As it turned out the vast majority opted for the high route. The wind was fierce.

We reach our first challenge at a curve in the path. About eight of us lie down anywhere that is half comfortable because the power of the wind is too strong. Along comes Conrad the Doc. I am delighted to see him because you can take turns walking in each others slip stream to get some relief from the wind.

It feels impossible at times as you raise your foot and the wind pushes you back and your foot lands in the same place or you stumble sideways. At one stage I was behind Conrad and desperately needed a break. Every step helped. Then you come to this part in the top of a mountain that is a real bummer — You go over the peak and down but then back up again.

We find the path is closed off because of snow drifts. I end up face down in a snow embankment. I jump up and end up being flung against the embankment. I jump up again and am really rolled around on the embankment. This time I surrender and slowly pull myself up to a half sitting position. My walking stick has doubled in two.

Down come three poor guys walking with their bikes. They were holding their bikes sideways using the wheels as brakes as the wind was catching the panniers. Then suddenly they were hit. All three ended up in an exposed embankment on the other side of the path lying on the ground. There was no panic. On the contrary most of us looked on the funny side of it.

In terms of energy drain it certainly was one of the hardest days I endured but I am glad I did it. Quite a few turned back and got taxis.`,
      image: "/camino/image9.jpeg"
    },
    {
      day: 28,
      title: "Zubiri to Pamplona",
      distance: "22km",
      highlight: "Journey complete - saying goodbye to Conrad and Philippe",
      content: `Still wet and muddy but another cake walk so I split with my two friends in Pamplona as they go on. That is the not nice part of the whole thing. I had become good friends with Conrad the Doc. and Philippe the Basque. We understood each other and went our own way at times to be alone but the company was very good and I spent two great weeks with them.

The three weeks prior to that were testing as several days I walked 35 plus km without seeing more than one or two walkers and in all this time when there was company it was invariably with non English speaking or individuals with very little English.

I noticed a young guy following us so I went back and introduced myself. He was Heiko from Hamburg. He liked our pace so I brought him into the company. He was a fine guy that worked as an aircraft mechanic.

I think the cafe and pub culture in Spain and France is very healthy. The owner of the bar or cafe is quite happy to have two people there for an hour. This morning Sunday the little cafes were full of people having their croissant and coffee. It is a big social occasion.`,
      image: "/camino/image10.jpeg"
    }
  ];

  const stats = [
    { icon: <Footprints className="w-6 h-6" />, label: "Distance", value: "~850km" },
    { icon: <Clock className="w-6 h-6" />, label: "Duration", value: "28 Days" },
    { icon: <Mountain className="w-6 h-6" />, label: "Elevation", value: "1,400m peak" },
    { icon: <MapPin className="w-6 h-6" />, label: "Route", value: "Le Puy → Pamplona" },
  ];

  const highlights = [
    { day: 1, text: "Finding Joyce's Irish pub in rural France", image: "/camino/image5.jpeg" },
    { day: 2, text: "13 hours lost in the mountains", image: "/camino/image3.jpeg" },
    { day: 7, text: "Beautiful medieval Conques", image: "/camino/image1.jpeg" },
    { day: 12, text: "Rest day in Cahors", image: "/camino/image2.jpeg" },
    { day: 26, text: "Conquering the Pyrenees", image: "/camino/image9.jpeg" },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section - Full Height */}
      <div className="relative h-screen">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(/camino/image9.jpeg)`,
            backgroundAttachment: 'fixed'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />

        <div className="relative h-full flex flex-col justify-center items-center text-center px-4">
          <Link
            to="/"
            className="absolute top-6 left-6 flex items-center gap-2 text-white/90 hover:text-white transition-colors bg-black/30 backdrop-blur-sm px-4 py-2 rounded-full hover:bg-black/50"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Home</span>
          </Link>

          <div className="max-w-4xl">
            <div className="mb-6 inline-block px-4 py-2 bg-amber-500/90 backdrop-blur-sm rounded-full text-white font-semibold text-sm">
              TRAVEL DIARY
            </div>
            <h1 className="text-6xl md:text-8xl font-bold text-white mb-6 leading-tight">
              Walking<br />the Camino
            </h1>
            <p className="text-2xl md:text-3xl text-white/90 mb-8 font-light">
              850 kilometers through France and Spain
            </p>
            <div className="flex flex-wrap justify-center gap-6 text-white/80 text-lg">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                <span>March - April 2012</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                <span>Le Puy → Pamplona</span>
              </div>
            </div>

            <div className="mt-12">
              <button
                onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
                className="animate-bounce bg-white/20 backdrop-blur-sm p-4 rounded-full hover:bg-white/30 transition-colors"
              >
                <ChevronDown className="w-6 h-6 text-white" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="relative -mt-20 z-10">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat, idx) => (
              <div
                key={idx}
                className="bg-white rounded-2xl shadow-xl p-6 text-center hover:shadow-2xl transition-shadow"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-white mb-3">
                  {stat.icon}
                </div>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                <div className="text-sm text-gray-600 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Introduction */}
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="prose prose-xl max-w-none">
          <p className="text-xl leading-relaxed text-gray-700 font-light">
            The following was my planned itinerary for the walk from <span className="font-semibold">Le Puy in France</span> (just south of Lyon) to <span className="font-semibold">Pamplona</span>.
            It was a little ambitious — lengths more than recommended so I allowed a few extra days for
            eventualities like bad weather. It starts in the <span className="font-semibold">Massif Central</span> — a high barren volcanic region — and goes
            south entering the lovely <span className="font-semibold">Lot valley</span> — then over the Midi Pyrenees — then over the Pyrenees and west
            to Pamplona.
          </p>
        </div>
      </div>

      {/* Photo Highlights Grid */}
      <div className="bg-gradient-to-b from-amber-50 to-white py-16">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-4">Journey Highlights</h2>
          <p className="text-center text-gray-600 mb-12">Memorable moments from the trail</p>

          <div className="grid md:grid-cols-3 gap-6">
            {highlights.map((highlight, idx) => (
              <div
                key={idx}
                className="group relative overflow-hidden rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer h-80"
                onClick={() => {
                  setExpandedDays(new Set([highlight.day]));
                  setTimeout(() => {
                    document.getElementById(`day-${highlight.day}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }, 100);
                }}
              >
                <img
                  src={highlight.image}
                  alt={highlight.text}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-6">
                  <div className="inline-block px-3 py-1 bg-amber-500 rounded-full text-white text-sm font-semibold mb-3">
                    Day {highlight.day}
                  </div>
                  <p className="text-white text-lg font-semibold leading-tight">
                    {highlight.text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Day Entries */}
      <div className="max-w-5xl mx-auto px-4 py-16">
        <h2 className="text-4xl font-bold text-center mb-12">The Journey</h2>

        <div className="space-y-6">
          {dayEntries.map((entry) => (
            <div
              key={entry.day}
              id={`day-${entry.day}`}
              className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow border border-gray-100"
            >
              {/* Card Header */}
              <button
                onClick={() => toggleDay(entry.day)}
                className="w-full px-8 py-6 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-6 flex-1 text-left">
                  <div className="flex-shrink-0 w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-bold text-xl shadow-lg">
                    {entry.day}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-xl font-bold text-gray-900 mb-1">{entry.title}</h3>
                    {entry.distance && (
                      <p className="text-sm text-gray-600 flex items-center gap-2">
                        <Footprints className="w-4 h-4" />
                        {entry.distance}
                      </p>
                    )}
                    {entry.highlight && expandedDays.has(entry.day) && (
                      <p className="text-sm text-amber-600 italic mt-2 font-medium">
                        ✨ {entry.highlight}
                      </p>
                    )}
                  </div>
                </div>
                <div className={`transition-transform flex-shrink-0 ${expandedDays.has(entry.day) ? 'rotate-180' : ''}`}>
                  <ChevronDown className="w-6 h-6 text-gray-400" />
                </div>
              </button>

              {/* Card Content */}
              {expandedDays.has(entry.day) && (
                <div className="px-8 pb-8">
                  {entry.image && (
                    <div className="mb-6 -mx-8">
                      <img
                        src={entry.image}
                        alt={entry.title}
                        className="w-full h-96 object-cover"
                      />
                    </div>
                  )}
                  <div className="prose prose-lg max-w-none">
                    {entry.content.split('\n\n').map((paragraph, idx) => (
                      <p key={idx} className="text-gray-700 leading-relaxed mb-4">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quote Section */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-600 py-20 my-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <blockquote className="text-3xl md:text-4xl font-light text-white leading-relaxed italic">
            "The mountains are beautiful but god you need to be back in civilisation every so often."
          </blockquote>
          <p className="text-white/80 mt-6">— Day 12, Cahors</p>
        </div>
      </div>

      {/* Conclusion */}
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-3xl p-12 shadow-lg">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Journey Complete</h2>
          <p className="text-xl text-gray-700 leading-relaxed mb-6">
            That completes stages 1 and 2 of the trail of St. James from Le Puy in France to Santiago —
            almost 1,000 miles. Stage 2 in 2008 and Stage 1 in 2012.
          </p>
          <p className="text-xl text-gray-700 leading-relaxed font-medium">
            It was lovely and thanks to everyone that helped.
          </p>
        </div>
      </div>

      {/* Travel Info */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
            <h3 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-3">
              <MapPin className="w-6 h-6 text-amber-600" />
              Getting Back to Dublin from Pamplona
            </h3>
            <p className="text-gray-700 mb-6 leading-relaxed">
              You need to get a bus from Pamplona to Bilbao and fly out from Bilbao. Bus costs around 17 euros
              and takes over two hours. Buy the ticket as early as you can to avoid the bus being booked out.
            </p>
            <div className="bg-amber-50 rounded-xl p-6">
              <h4 className="font-bold text-gray-900 mb-4">Bus Timetable (La Burundesa)</h4>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="font-semibold text-gray-700 mb-2">Mon-Sat:</p>
                  <p className="text-gray-600 text-sm leading-relaxed">7:00, 10:00, 13:00, 15:30, 18:00, 20:30</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700 mb-2">Sun & Bank Holidays:</p>
                  <p className="text-gray-600 text-sm leading-relaxed">9:00, 11:15, 16:00, 17:30, 20:00</p>
                </div>
              </div>
              <p className="text-gray-600 text-sm mt-4 leading-relaxed">
                From Pamplona central bus station at Park Castillo (underground). Airport bus from Bilbao
                costs less than 2 euros compared with 25 euros plus for a taxi.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-gray-400">
            A personal travel diary documenting the ancient pilgrimage route
          </p>
          <p className="text-gray-500 text-sm mt-4">
            March - April 2012
          </p>
        </div>
      </footer>
    </div>
  );
};

export default CaminoPage;
