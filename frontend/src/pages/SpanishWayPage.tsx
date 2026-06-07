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

  const stages: StageEntry[] = [
    {
      stage: 1,
      title: "Irun to San Sebastian",
      route: "Irun → San Sebastian",
      distance: "26.5km",
      region: "basque",
      excerpt: "First day. Brutal climbs. 1000 steps up a cliff. Views over Bay of Biscay. San Sebastian on fire with Friday night crowds.",
      content: `Stayed in hostel last night --- Albergue de Peregrinos at Calle Lucas de Berroa. I learnt my first lesson -- the cost was a voluntary donation interpreted generally as 5 euros. I only had 20 euros. I ask for change. There is no response. There is a queue waiting behind me so I feel under pressure to put the twenty in the slot in the box still half expecting the change --- it never came. So if the hostel is by donation have change like a five euro note or a ten euro note.

The hostel was ok but I shared the room with two rough elderly French men who snored like a donkey roars. Irun was a lovely little town. It is just inside the Spanish border. The guide said the climbs in day one were brutal and so it was one after another. At one stage we had to go up a sheer cliff by steps near a light house well there must have been 1000 steps. The sweath was pumping but the views over the bay of Biscay were stunning.

I met this 40 plus something ecentric Spaniard walking against me and I checked the map with him but just in case he turned around and walked about 6 miles with me. There was this town hidden away down by the riverside called Pasajes de San Juan. It was really quaint. Real narrow streets with little bars. From there I had to get a boat across to the other side .65cents it cost.

San Sebastian is built on a beach with this enormous Plaza all the way between the strand and the city. It is beautiful. I had a room booked here as the hostel was out of town. I was in the old quarter. It is Friday night and the place is on fire with crowds inside and outside the bars everywhere. I had some lovely Tapas. You can smell the wealth everywhere. The room cost me 42 euros. This was the most I paid for the entire journey but it was in the perfect place in a great city.`,
      image: "/camino/image1.jpeg"
    },
    {
      stage: 2,
      title: "San Sebastian to Zumaia",
      route: "San Sebastian → Zarautz → Zumaia",
      distance: "30km+",
      region: "basque",
      excerpt: "Over a stage and a half. Walking on the coast. Passing Zarautz. Zumaia smack in the centre for 20 euros.",
      content: `Nice day. Bit of rain. Walking on the coast. Scenery special. I come to a lovely town Orio and stay going. I reach Zarautz. It is lovely. I see a big hotel and I think maybe I can bargain with them. There is a lovely receptionist and she asks nicely if I know it is Sat night and it is very hard to find a bed anywhere. I keep walking.

Before I know it I am out of the town passing my stage stop and I stay going as I feel ok. There is this walk like the Liffey boardwalk in Dublin. Here it is between the road and the sea and it goes from one town to the next. I get to a town called Getaria. It is lovely. I stay going as I am going to try and do three days stages in two now ie a stage and a half per day. I am trying to shake off the two French men as well.

I stop in a lovely town called Zumaia. I get a bed smack in the centre for 20 euros. It is a really fine place. Find the centre of town------- there will be a few busy pubs esp at weekend walk up to counter relax and get the bag off the back and have a coffee. In this case in Zumaia the pension was in the second floor of the bar that I was in --- out the door around the back and up two flights of stairs. The place was again on fire with crowded pubs. Todays ascent was 520 metres.`,
      image: "/camino/image2.jpeg"
    },
    {
      stage: 3,
      title: "Zumaia to Markina-Xemein",
      route: "Zumaia → Deba → Markina-Xemein",
      distance: "40km+",
      region: "basque",
      excerpt: "One of the hardest days. Fell twice in the muck. 915m ascent in rain and mist. 10 rough hours. Matron trouble at the convent.",
      content: `This became one of the hardest days I spent on the mountains. I am thinking of walking a stage and a half to make up a full day. The first half stage has its usual rough climbs and rough descents. Its raining and there is no shortage of muck so I tumble twice-- not nice for the confidence especially when you are soaked in muck. It is not uncommon to fall of course as I later discovered.

I reach the half stage mark a town called Deba ie with a full stage to go if I keep on walking --- the descent into the town is so bad that they have installed a lift to bring you down. I have a coffee and I can see the pool of muck building up from my shoes. I can see the hostel in the town. It is Sunday as well and there is a mighty temptation to call it a day.

The next stage is about 20 miles significantly longer than what the guide says. The ascent is mighty 915 metres. It is raining and the last half of the journey has no food; no water; no nothing. The route was something else mighty ups followed by mighty downs non stop. There was no sign of other walkers. Then the mist came thick making it very hard to see signs or outlines. Luckily the mist lifted after about an hour.

Reached town destination called Martina- Xemein after 10 rough hours going. There is no hotel or Pension so I have to settle for this austere lovely convent. On arrival I get into trouble immediately with the matron. I just want to get into a shower -- I see one and I jump in. A lady comes in and does oh la la bit and goes out again to arrive back in with the matron. I am in a ladys shower room and she orders me out. The matron then followed me to the dormitory and hit me for ten again. I was sleeping in the bottom bunk but had my coat hanging from the rail of the top bunk ---- not allowed stick to your space. Later I get on great with the Matron and staff. She asks me to say a prayer for her in Santiago.`,
      image: "/camino/image3.jpeg"
    },
    {
      stage: 4,
      title: "Markina-Xemein to Gernika",
      route: "Markina-Xemein → Gernika",
      distance: "25km",
      region: "basque",
      excerpt: "Meet Brian, Rosemary, and Jim from Ireland. Monster dogs, Muslim signs. The Basque are merchants and industrialists.",
      content: `No more stage and a half stuff I think --- for now at least. A stage here tests you far more than a stage in the other Camino routes. I feel ok except feet -- a few badly crushed toes from the descents. Still a lot of muck. I see signs like Muslims out and no fracking here. There must be a problem with house theft as any kind of decent house has these monster dogs wired in around the outside of the house. When they bark the ground shakes with the fence. France had the same everywhere also.

I have met no English speaker until today so I meet Brian and Rosemary from Newcastle Co Down and Jim Booth from North Caroline. We get on very well. We arrive in town and after a few enquiries we find the right pub with the right man who controls the Pension so we get simple rooms for 30 euros.

I go into a pub. I meet a Basque who was born in Australia. He teaches English now. There is a pub in town run by a Tipperary man. He wants to bring me there but I decline. From Irun to here you can smell riches everywhere -- mansions of houses -- no run down areas. The Basque explains that Basques are pretty rich. They are merchants and industrialists. I used to think they were simple mountain people. He refers to the problems of Southern Spain being a drag on the country. The Basques father was a sugar cane cutter in australia. That must have being one of the roughest jobs on earth.`,
      image: "/camino/image5.jpeg"
    },
    {
      stage: 5,
      title: "Gernika to Bilbao",
      route: "Gernika → Bilbao",
      distance: "35.5km",
      region: "basque",
      excerpt: "Worst day of muck. 835m climb. Jim tells his wife three times how much he loves her. Farewell to Brian and Rosemary.",
      content: `This is 35.5Km but the guide book says if possible staying going to Portugalette. This would add another 10.5 Km which we all say no thanks. Today is the worst day of muck -- a sea of it. Each day the climbs go on and on. Today we go up 835 metres and the description of difficulty is one notch from most difficult.

Jim got on his Ipad last evening while we were having a drink and he told his wife in an overemotional way three times how much he loved her. I raise this with him this morning saying I could but not have heard him telling his wife how much he loved her. I say that was very nice but I would find it hard to say this as there was no point as she should know it anyway and I would fill a bit of a sissy. That gave Jim an opening for the next three hours to talk to me about the errors of my ways.

There was a mighty climb before Bilbao --- to see the city from one of the peaks around it --- It was misty and you could see very little. We said farewell to Brian and Rosemary. They are going home from here. Jim and myself proceed to this hostel just outside the western suburbs. It is an old Primary school with these tiles that give it a cold cold feeling. Jim informs me he wants to take at least one day out so I am on my own again.`,
      image: "/camino/image7.jpeg"
    },
    {
      stage: 6,
      title: "Bilbao to Pobena",
      route: "Bilbao → Pobena",
      distance: "22km",
      region: "basque",
      excerpt: "Waymarking score: 5 out of 5 (useless). Walking alone. 17 beds, over 40 pilgrims. Germans explain their shopping bags.",
      content: `The guide book says the waymarking on a scale of 1 to 5 is five that means it is no use. That helps greatly next morning as I am all alone and come to the first fork with no signs. Somehow I got it right. For the last 8 miles I link up with a Spaniard who has zero English.

We pass a nice town Playa De La Arena and a half Km on is Pobena with just one hostel. The place and the town look very well. I book into hostel in Pobena. It is now getting a bit hectic. There are over 40 between cyclists and walkers on the stage I am on. This hostel has 17 beds. I am fine because I am early but about 10 are put sleeping on the floor. When that fills up they try sending them to hotels in nearby towns.

The Germans are so straight. One German comes back to the hostel having gone to the next town 1 km away to shop. I say not seriously what is in those bags. He drops the two bags takes out everything and explains to me what he has got.`,
      image: "/camino/image8.jpeg"
    },
    {
      stage: 7,
      title: "Pobena to Castro-Urdiales",
      route: "Pobena → Castro-Urdiales",
      distance: "17.5km",
      region: "cantabria",
      excerpt: "Beautiful day. Mist rising in Bay of Biscay. Spectacular cliff paths. Castro-Urdiales is special. Room for 40 euros.",
      content: `I get up early and head off mixing with two Spaniards. We arrive very early 11am. The day is beautiful. The mist is rising in the bay of Biscay around the cargo ships waiting to go into Bilbao. Spectacular paths are developed on the cliffs by the sea. There are posters explaining the different types of fish in the bay and other posters explaining the wild life. There is a walkway/cycle lane all the way. There are lots of locals walking and cycling.

Castro Urdiales is special city. It is like the others a semi circular beach -- the city built around it and a special plaza in between. Tonight in the restaurant overlooking the harbour a couple in their sixties sit in front of me and she has a beer and he has a coffee.

My crushed toes are not great. After a bit of effort I get a Habitacion (room) in the right spot bang in the centre for 40 euros. I get a bit of help from one of the Spaniards. He has detailed notes of all the alternatives with multiple phone numbers for each location. The hostel is in the suburbs so why would you want to stay in the suburbs of a great town.`,
      image: "/camino/image10.jpeg"
    },
    {
      stage: 8,
      title: "Rest Day in Castro-Urdiales",
      route: "Castro-Urdiales",
      distance: "0km",
      region: "cantabria",
      excerpt: "Feet needed a break. Got 'dipped' - mobile phone stolen. Mickey mouse replacement. Plate of squid for 7 euros.",
      content: `It does not exist yet. I have to give the feet a break for a day. Thanks to Reddys chemist and Dr Cox and their medicines ----- a few hours later and the pain is going and the feet are moving and I hope I will be ready tomorrow.

The feet were not the only problem. I went into an internet cafe for the unemployed and got "dipped" mobile phone gone. I should have copped it he let on he had not enough space to pass behind me and pushed my chair -- my music -- my contacts. Ah to hell with it its not the end of the world. I go into a library and get access to emailing so I end up getting Mary and my sons Niall and Kevin to help out. Son no 3 Brendan is on a different shift in Aussie. I get a new mickey mouse phone to get by and I stop feeling sorry for myself.

I go to this beautiful pub/restaurant that I was in the previous night and a barman was very nice so I tipped him. He was up to form again tonight--- I was grabbing Tapas and he said no special is plate of squid and he went off and got me a hot plate of squid with bread for 7 euros. It was great. I spent the second night in the same Habitacion.`,
      image: "/camino/image1.jpeg"
    },
    {
      stage: 9,
      title: "Castro-Urdiales to Laredo",
      route: "Castro-Urdiales → Laredo",
      distance: "30km",
      region: "cantabria",
      excerpt: "Up early. Girl wobbling at 7am. Arrived at noon. Franciscan monastery for 13 euros. Football team marching. Bilbao vs Barcelona.",
      content: `Up early because of foot problem plus forecast to be warm. The crowds were everywhere last night -- Friday night. As I head out of town 7 o clock this girl is wobbling in front of me. I pass her but she shouts the time please. I tell her and she goes oh le la.

The day turned out perfect. I took two low risk short cuts and they ended perfect. I arrive in beautiful Laredo at 12 o clock. Thinking I was doing great I met 4 from Tullamore who left later than me but arrived with me. I book into a Franciscan place called Buen Pastor for 13 euros. A nun is in charge. She takes 10 minutes to come to the door. She does not have a word of English but I get on with her like a house on fire. It is beautiful old world monastery with great space and all the religious emblems.

The local foot ball team were playing so these armies of guys out to enjoy themselves are everywhere -- banners -- colours-- drums. There is a big spring in their step as they march along. Tonight Bilbao play Barcelona in the cup final and that is so important that the curfew in the hostel is lifted.`,
      image: "/camino/image2.jpeg"
    },
    {
      stage: 10,
      title: "Laredo to Guemes",
      route: "Laredo → Santona → Guemes",
      distance: "30km",
      region: "cantabria",
      excerpt: "Ferry at 9am. Prison that goes on forever. Beach for miles. Offaly gang! Ernesto's hostel with theology lecture and communal dinner.",
      content: `Up early and you need a ferry to get to the next town Santona. Bad luck it is Sunday morning and the first ferry is 9am. The ferries cost very little like 2 euros. The signs are hopeless today. Santonia has no signs. Just past Santonia there is this prison that goes on for ever -- it is enormous. The track luckily then is along a beach and it goes on for miles. I stop in a nice town Noja for a coffee and a sandwich.

I meet up with Offaly gang and we decide to head for an isolated hostel in Guemes with religious undertones. The Offaly gang are three Coughlan sisters from Clonfert --Lil is married to Denis Coughlan who runs Friars Tavern in Larrha. He is 71 and going strong -- Charlie Mc Donnell from the other side of Black sod bay in Mayo is married Bridget and they live in Tullamore ---Josie is married to Kevin Cassidy Kilcormac and Kevin stayed at home. The final member was Jim Mollahan -- the Fuhrer or leader from Tullamore --- Jim was a former teacher.

After a long walk we eventually reach the hostel --- it is beautiful --- we notice a beautiful room for reflection and another room for Bible reading. Ernesto Bustio a 78 year old runs the show. He has an eternal smile as do all the staff. He studied theology late in life and he gave us a lecture on the world in general and his role and his travels. It lasted one hour. There was no mention of god. Eventually we got to this communal dinner --- three mighty bowls of soup with a bucket of bread followed by a big stew. It was super. The cost for all that was a voluntary donation.`,
      image: "/camino/image3.jpeg"
    },
  ];

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

      {/* Featured Stages - Magazine Grid */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h2 className="text-5xl md:text-6xl font-black text-stone-900 mb-4">The Journey</h2>
          <p className="text-xl text-stone-600">31 stages along Spain's northern coast</p>
        </div>

        <div className="space-y-24">
          {stages.map((stage, idx) => (
            <article
              key={stage.stage}
              className={`grid md:grid-cols-2 gap-8 items-center ${
                idx % 2 === 1 ? 'md:grid-flow-dense' : ''
              }`}
            >
              {/* Image */}
              <div
                className={`relative group cursor-pointer ${
                  idx % 2 === 1 ? 'md:col-start-2' : ''
                }`}
                onClick={() => setSelectedStage(selectedStage === stage.stage ? null : stage.stage)}
              >
                <div className="relative overflow-hidden rounded-3xl shadow-2xl aspect-[4/3]">
                  <img
                    src={stage.image || '/camino/image1.jpeg'}
                    alt={stage.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />

                  {/* Stage Badge */}
                  <div className="absolute top-6 right-6">
                    <div className={`bg-gradient-to-br ${regionColors[stage.region]} text-white px-6 py-3 rounded-2xl font-bold text-lg shadow-2xl`}>
                      Stage {stage.stage}
                    </div>
                  </div>

                  {/* Distance Badge */}
                  {stage.distance && (
                    <div className="absolute bottom-6 left-6">
                      <div className="bg-white/90 backdrop-blur-sm text-stone-900 px-4 py-2 rounded-full font-semibold text-sm flex items-center gap-2">
                        <Footprints className="w-4 h-4" />
                        {stage.distance}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className={idx % 2 === 1 ? 'md:col-start-1 md:row-start-1' : ''}>
                <div className="space-y-4">
                  <h3 className="text-4xl md:text-5xl font-black text-stone-900 leading-tight">
                    {stage.title}
                  </h3>

                  <p className="text-xl text-stone-600 leading-relaxed font-light">
                    {stage.excerpt}
                  </p>

                  {selectedStage === stage.stage && (
                    <div className="prose prose-lg prose-stone max-w-none pt-4 border-t-2 border-stone-200">
                      {stage.content.split('\n\n').map((paragraph, pIdx) => (
                        <p key={pIdx} className="text-stone-700 leading-relaxed">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={() => setSelectedStage(selectedStage === stage.stage ? null : stage.stage)}
                    className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold group mt-2"
                  >
                    {selectedStage === stage.stage ? 'Show Less' : 'Read Full Story'}
                    <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>

      {/* Journey Stats */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { icon: <Coffee className="w-8 h-8" />, number: '31', label: 'Days Walking', detail: 'Irun to Santiago' },
            { icon: <Users className="w-8 h-8" />, number: '6', label: 'The Offaly Gang', detail: 'Denis, Lil, Josie, Charlie, Bridget, Jim' },
            { icon: <Heart className="w-8 h-8" />, number: '817.5', label: 'Kilometers', detail: 'Along the northern coast' },
          ].map((stat, idx) => (
            <div key={idx} className="text-center p-8 bg-white rounded-3xl shadow-xl hover:shadow-2xl transition-shadow">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-400 to-teal-500 rounded-2xl text-white mb-4">
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
          <h2 className="text-4xl md:text-5xl font-black mb-6">The Northern Way</h2>
          <p className="text-xl leading-relaxed mb-6 text-white/90">
            The scenery in the Northern route is spectacular exceeding my expectations but these beautiful mountains and valleys everywhere have a price ie there are non stop tough climbs and tough descents. You will get away with a bit of training in the French Camino but up North you need to have trained very hard.
          </p>
          <p className="text-2xl font-light text-blue-400">
            Thanks to everyone that helped.
          </p>
        </div>
      </div>

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
