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
    {
      stage: 11,
      title: "Guemes to Santander",
      route: "Guemes → Somo → Santander",
      distance: "24km",
      region: "cantabria",
      excerpt: "Ferry crossing. Extended day with cliff and beach walks. Offaly gang's final day. Celebrated together in Santander.",
      content: `I head off with Offaly gang -- today it is supposed to be 17Km but we up it to 24 to get this big cliff walk and beach walk in. We get ferry from Somo to Santander. Arrived good and early. City is fine but it would not be my no 1 of the places so far --- maybe I did not see enough of it.

We all book into a Pension in the centre - Hospedaje in Isabel 11 ( near the Cathedral and metres from the route out of the city). It is the Offaly gangs final day walking so lets say we celebrated. To make matters worse they paid for my meal. It is nice to meet nice people like that along the route -- the problem then is you split up. The girl in charge of the Pension needed to be shaken up.`,
      image: "/camino/image5.jpeg"
    },
    {
      stage: 12,
      title: "Santander to Santillana del Mar",
      route: "Santander → Santillana del Mar",
      distance: "32.5km",
      region: "cantabria",
      excerpt: "Long walk out of city. Direction signs on pavement. One of Spain's most beautiful medieval towns. Beautiful pension for 20 euros.",
      content: `I am out of bed at 6.30 and ready to go. I have told Offaly gang I will say a prayer for them in Santiago. The girl at reception in the Pension was lets say slow. Now this morning the internal door of the building is locked and I need to find her which I do in the room behind reception -- she is not happy to have her dreams disturbed. There is a restaurant open next door so I have a cup of coffee.

I head off in the long walk out of the city. The direction signs here are on the pavement. Sometimes you come to a junction and there is no direction sign ---- or so you think. 90% of the time if you reverse a little and look at everything a little closer you will find a direction sign. The numbers are down--- I only see a few other walkers.

I arrive in Santillana around 2pm. Santillana is known as one of Spains most beautiful towns with narrow streets. 20 years ago there were cattle in the ground floors of these houses. Now it is a mecca with tourists everywhere. A bus unloads as I pass and there is a rush in my direction -- I am the only pilgrim in sight ---- they want a photo with the pilgrim. I went for my first menu del dia tonight --three mighty courses and wine ad lib for 12.9 euros.`,
      image: "/camino/image1.jpeg"
    },
    {
      stage: 13,
      title: "Santillana del Mar to Comillas",
      route: "Santillana del Mar → Comillas",
      distance: "23km",
      region: "cantabria",
      excerpt: "Country walking. Coffee and omelette for 2.25 euros. Gaudi's architecture. Menu del dia for 9 euros. Dogs everywhere.",
      content: `In the country today away from towns. I called into the first bleak bar -- no food and some kind of kettle. I turned around and walked on until I found a nice place --- a cup of coffee a slice of their omlette and a lump of bread all for 2.25 euros. I hit town at 12 and get a nice room near the middle of town in Hostal Esmeralta for 35 euros.

This town was the seaside resort of the wealthy from Barcelona and they hauled along the designer Gaudi whose work you can see. I have plenty of time so I call into a bar for a celebrated beer. It is lunch time. They stack me up with food -- no money.

It is a lovely town. Again in every café or bar groups come in and have a coffee or drink. It looks like nobody can walk a dog without calling in for a beer or wine. Dogs are everywhere. It seams to be a security issue. I get menu del dia for 9 euros. It was great.`,
      image: "/camino/image2.jpeg"
    },
    {
      stage: 14,
      title: "Comillas to Buelna",
      route: "Comillas → Colombres → Buelna",
      distance: "35km+",
      region: "asturias",
      excerpt: "Railway bridge shortcut. Extended to Buelna. Private hostel with Mexicans. Dutchman and Austrian taxi driver. Rain and wine.",
      content: `I am getting in on the act of how to take a short cut. In one place you have to go off to one side of a river for 2km and to get a bridge and then 2km back again but there is an alternative ----- there is a railway bridge crossing the river directly on your track. Only problem is you must get on the tracks and then you go a fair distance on the tracks before you can get off them at the next railway stop. I go for it.

I arrive in good time in Colombres which is in Asturia. The climb up to it was mighty. The hostel was a dreary old school so I keep going. I have done 28.5km but I feel fine. I go through the next town La Franca and 6km from Colombres when I need it there appears this perfect hostel in a place called Buelna. 15euros for dinner bed and breakfast --- a lovey mother and son aided by 3 mexicans.

The rain comes pouring down and old mama grabs everything from the lines and puts them into the drier. The hostel has a bar also which is great.`,
      image: "/camino/image7.jpeg"
    },
    {
      stage: 15,
      title: "Buelna to Ribadesella",
      route: "Buelna → Nueva → Ribadesella",
      distance: "42km",
      region: "asturias",
      excerpt: "Almost 50km in guidebook. Split from Dutchman and Austrian at 33km. Pushed on alone. 42km total. Beautiful man at Hotel Marina.",
      content: `This is almost 50 km in the guidebook. The only three going to try it are yes the Dutchman, the Austrian and myself. I go through the maps to organise short cuts to bring it down to the low 40s. The Dutch man does his homework also. It is raining also. We start early.

We stop a second time for coffee to evaluate progress. I detect that my friends will not make it to Ribadesella but I say nothing. 33 km into the journey in a village called Nueva the Dutchman announces he has had it and that he will negotiate a price for a triple room. The Austrian agrees readily -- there is no hostel. I announce that I feel fine (not entirely true) and that I will go on. I know if I can make it to Ribadesella I will have taken a day off the trip. He did not like it but I got satisfaction out of it.

It was a hard slog and the last 5km were lets say hard. hard hard. I did 42/43 km. I arrived in Ribadessella and started studying the map. This lovely Young guy comes up and says do you need help. There is this beautiful man at reception and he says I will give you a very good room for 35 euro and I will get you a good breakfast also.`,
      image: "/camino/image8.jpeg"
    },
    {
      stage: 16,
      title: "Ribadesella to Villaviciosa",
      route: "Ribadesella → Sebrayo → Villaviciosa",
      distance: "42km",
      region: "asturias",
      excerpt: "Sebrayo is an outpost with only water and bed. Not spending Saturday there. 42km to Villaviciosa. Hill Billy night.",
      content: `I discoverd that sebrayo is an outpost in the hills. There is wáter available and a bed. nothing else nearby ---no food no shop no beer. I am not going to spend Saturday night their so I set my eyes on Villaviciosa another day of around 42km. It rained and it was cold esp in the mountains. For parts of it I am on unmarked territory. At one stage I was unable to verify my position for a long time but it turned out fine in the end.

I booked into a hostal (an unclassified hotel) 15 euros for the bed. It is fine. Again the hotels and hostal are in a cluster in the middle of town after a long walk in to town. I do say a prayer for everyone in the Little churches. I judged villavicosa and gave it too much credit earlier ---- every second bar and cafe had a tv blazing in the afternoon with two or three people that looked down on their luck blankly staring at the tv.

It came to night time. Every Hill Billy within 50km must have being in town. Very little sleep - shouting in the street. Missing steps on stairs and falling. Then one person at 4 puts on blaring music.`,
      image: "/camino/image10.jpeg"
    },
    {
      stage: 17,
      title: "Villaviciosa to Gijon",
      route: "Villaviciosa → Gijon",
      distance: "35.5km",
      region: "asturias",
      excerpt: "Gigantic bowl climb. French woman: 'You're looking for miracles - Ernesto never mentioned God in three weeks.' Road into Gijon went on forever.",
      content: `Gijon is a big city so I am looking forward to this. The walks in the last few days have being reasonable but at 7.30 this morning it feels like being in a gigantic bowl. You kind of think there must be a half gap somewhere up their that I cannot see yet. There was not-- it was pumping sweath all the way -- twice two climbs.

On one occasion I was pondering between two directions on mountain top when along came a tough 30 something French woman. She is not sure from her guide either. We spoke about religion and she said she was spiritual. I asked what that meant in practice and she agreed that was difficult question to answer. Now for my Offaly gang she said she worked as a volunteer for three weeks with the Padres hostel in the mountain. I said he spoke for one hour but never mentioned god. She said you are looking for miracles I was with him for three weeks and he never mentioned god.

The road into Gijon went on for ever like 5 miles. For the first time I got disorientated as to the right direction in the city. The local team was playing and won and there was a great party in town. The Corpus Christi procession was on and boy was there colour.`,
      image: "/camino/image1.jpeg"
    },
    {
      stage: 18,
      title: "Gijon to Aviles",
      route: "Gijon → Monte Areo → Aviles",
      distance: "24.5km",
      region: "asturias",
      excerpt: "Industrial territory. Miles of massive factories. Author calls it ugly - they make products we all enjoy. Evangelical man in hostel.",
      content: `Another big town or city. We are in industrial territory now with miles of massive factories and working class estates. The author in my Cicerone guide is good in most respects but he finds all this distateful using terms like you could be forgiven for getting a bus to bye pass this ugly scene. He should get real these people make the everyday products we all enjoy. This is also a Christian journey and he should think a bit more Christian.

It is one day out of 30 plus days and I enjoyed trying to figure out what all the factories were making. God they were enormous like miles with their own railway tracks etc. There was a mighty climb mid morning to what is called the Monte Areo. At one stage I was confused and saw a local and double checked. Lucky I would have made the wrong decision and added a few km.

Arrived in Aviles and in this big hostel there is another evangelical man from Chicago half way down the garden to greet me. 5 euros for the bed. I know no one in the hostel and have seen very few walkers in the past few days.`,
      image: "/camino/image3.jpeg"
    },
    {
      stage: 19,
      title: "Aviles to Soto de Luina",
      route: "Aviles → Soto de Luina",
      distance: "45km+",
      region: "asturias",
      excerpt: "Detour disaster. Road ended on stilts in the air. Had to walk around motorway via coast. 45km+ day. Fionnan from Dunshaughlin!",
      content: `Set off early as it is a 39Km walk. It is misty so my poor guide is getting raggy. I try a few detours and they work. Then I try another --- I was dumb I was on this minor road and then it was blocked with bolders. I could easily have switched to the official route which ran parallel but no I wanted to see where this road was going. There was grass growing on the road so it should have being obvious it was going no where which was the case -- it once was connected to the motorway now it ended on stilts up on the air.

My town is somewhere on the other side of the motorway. To make a long story short the only way to get across the motorway was to my village as I discovered was to walk through two more villages then go to the coast go around the headland and come back the other side of the motorway ---45 km plus day I would guess.

Hostel is fine 5 or 6 euros. A bit of the language helps as here I found out the hostel was run by the local publican so you had to go to the pub to register. Around 8.30 the first person from Ireland that I met in some time staggers tiredly in the door having being on the trail all day. He needed a bed quickly. He was from Dunshaughlin in Meath his name was Fionnan Tuite.`,
      image: "/camino/image5.jpeg"
    },
    {
      stage: 20,
      title: "Soto de Luina to Luarca",
      route: "Soto de Luina → Cadavedo → Luarca",
      distance: "36km",
      region: "asturias",
      excerpt: "Bad marking. French snorers - found one earplug. Beautiful seaside town in basin. Steps everywhere. 360 miles walked, 151 to go.",
      content: `This was a 36 Km walk with bad marking but territory not too tough. I walked with Fionnan. He is a teacher in Dublin. Normally during the day survival is an odd snack or an orange and a big meal at night. There was a problem in the hostel last night -- a group of French --boy did they make noise in their sleep. I never used the ear plugs but tonight I got out of bed to search for them. I could only find one so I put the ear with no plug on the pillow and managed fine.

Met a nice young guy from Israel today Nadav -- he is 25 -- but up to now it is mostly the Germans that I have the craic with. I book into a fine hostel for 10 euros in a fine sea side town. It is beautiful. Fionnan going home tonight so I am on my own again. This is a beautiful town. It is based in the bottom of a basin with a marina and steps in their hundreds down to the town.

The good news I have walked now 360 miles with 151 miles to go.`,
      image: "/camino/image7.jpeg"
    },
    {
      stage: 21,
      title: "Luarca to La Caridad",
      route: "Luarca → La Caridad",
      distance: "31km",
      region: "asturias",
      excerpt: "Young guy zooms past. American Norman teaching English. Beautiful hostel for 10 euros. Bread and cheese dinner.",
      content: `Nice day 31 Km and I got in very early. At one stage I was walking with a French guy behind me and this young guy came along and zoomed past. My heart sank a bit at the ease he passed us but it did not last he had just upped the speed to get past us. I got up with him again and finished the day with him.

I met a young American from Maryland who was teaching english in Spain but was now going back to US. I asked him if he was getting real and he said yes. His name is Norman McKay Teaching English is a kind of lifestyle -- small money. he said those that work in grind schools make big big money like 2,000 euros a month. I wonder what would Irish teachers think of that.

The hostel is beautiful for 10 euros. It is on the edge of town. I wander all over town and cannot find a proper meal so I go to the supermarket and get a lump of bread and cheese. I should have stayed with the gang in the hostel as they all went to a different place for a pilgrims menu and had a great night.`,
      image: "/camino/image8.jpeg"
    },
    {
      stage: 22,
      title: "La Caridad to Ribadeo",
      route: "La Caridad → Ribadeo",
      distance: "21.5km",
      region: "galicia",
      excerpt: "German brothers gone with ankle injury. Drifted onto coastal route by mistake. Ribadeo in Galicia. Boss at hotel so helpful.",
      content: `SINCE THE BEGINNING I HAVE BEING WALKING ON OFF WITH DIFFERENT INDIVIDUALS. there was three germans around my age. they walked military style one behind the other. I got on great with them but in luarca one of the brothers came over to me to say the other one had gone over on his ankle. When the grub was over I went over to them and wished them well. They were hoping for the best but our parting resembled a final departing. It was sad.

I saw Nadav heading off early this morning. I shouted at him -- no point I will catch you. I said to Nadav that our journey did not look right. We were too near the sea and the wrong side of the highway. Nadav slows behind me studying the map and then comes up saying do you want the good news or the bad news. The good news was the weather was great. The bad news I knew -- we had drifted on to the coastal route.

We are in Galicia now which is like remote rural Ireland in the 50s. I offer to pay the hotelier as I book in --- he says no you pay later and put that plastic card away I prefer money. The boss doubled as a receptionist/waiter and barman. Heading out the door of hotel at 7 and who is their at the bottom of the stairs except the boss to shake hands and offering me a free coffee.`,
      image: "/camino/image10.jpeg"
    },
    {
      stage: 23,
      title: "Ribadeo to Lourenza",
      route: "Ribadeo → Lourenza",
      distance: "27.5km",
      region: "galicia",
      excerpt: "Boss on balcony wishing well. 1000-year-old monastery. Cute woman drags me to marble room. 38 euros. Major dislike to plastic money.",
      content: `Heading out the door of hotel at 7 and who is their at the bottom of the stairs except the boss to shake hands and offering me a free coffee ---- he will never see me again and yet he is so helpful pointing the way out of town --- they are long days for that man. Did journey in great time. Lourenza has a beautiful 1000 plus year old monastery.

There is a sign coming into town for a rural Casa or country house. It is on the edge of town so I said I will try it. The woman was as cute as hell. She listened to nothing dragging me to this room. It was all in marble --- fridge with orange juice milk etc. She says leave the bag and she shows me the kitchen beautiful again. I am always asking quanto or how much but that she ignores until the end when she knows I will not put that bag on my back again today. 38 Euros but it was worth the experience.

That night the boss man insists I sit down for a half an hour while he goes through all the options for the week ahead --phone numbers -- options for accommodation. Again when paying I am told they have a major dislike to plastic money then he looks at me and giggles kind of saying you understand.`,
      image: "/camino/image1.jpeg"
    },
    {
      stage: 24,
      title: "Lourenza to Gontan",
      route: "Lourenza → Abadin → Gontan",
      distance: "24km",
      region: "galicia",
      excerpt: "Boss on balcony wishing well. Steepest 2km climb in Spain. Deserted villages. Cleaning cow dung. Beautiful hostel 6 euros.",
      content: `As I leave prior to 7 there on the balcony is the boss wishing me well ----- what attention to detail these people have. My fridge was topped up with juice and Pastrys. I took three of the pastrys and boy were they good in long stretches with no cafes.

Meeting up with Norman and Nadav on and off. I have not seen the German brothers since. There is about 25 people walking every day in my stage now. This morning as I walk alone in the country side a young guy about 14 going to school comes up to me asks where am I from, where did I start, where an I going and why. He was a lovely guy.

To day there is incredible scenery but it comes at a price -- the steepest 2km climb of all the Caminos in Spain is just one challenge. I get bye fine. We are now going to spend a few days going up. There are deserted and dying villages along the route. As if to emphasise it the signs for the villages are fading away in tandem with the village. I see two ladys cleaning out the cow dung with a wheel barrow Got a beautiful hostel in Gontan for 6 euros.`,
      image: "/camino/image2.jpeg"
    },
    {
      stage: 25,
      title: "Gontan to Baamonde",
      route: "Gontan → Vialaba → Baamonde",
      distance: "40km",
      region: "galicia",
      excerpt: "40km managed by 3pm. Big angry American: 'This Camino is shit!' Screams for taxi. I ignore advice to walk 1km extra.",
      content: `Still doing long days. Today is 40km again but I manage and I get home at a highly respectable 3pm. The hostel is 6 euro. Walked with Norman and Nadav on off. I stop in a town Vialaba and I murder two sandwitches and a coffee. I make up evenig grub for 2.8 euros. I get bored of the pilgrim menues.

This morning as I walked I saw this very big man in front of me -- 6foot 5inches and twenty five stone. He is struggling. I have not seen him before. He has a mate that is half his size and looks well equipped. I salute as I pass the big man as usual but this time I do not even get a grunt for a reply. He then snarls at his mate to come back which he obediently does -- no question about who is the boss.

I call into a lovely cafe at the cross roads a km later. I am in the middle of the sandwitch when the big man and his mate come crashing in. They speak German but the big man has american English. I go up for the hell of it and shake their hands. The big guy screams at me what you think of this Camino -- without waiting for an answer he says I am telling you it is s---. The camino is over. The little man is cringing. Ten minutes later the taxi called and there is the sad ending.`,
      image: "/camino/image3.jpeg"
    },
    {
      stage: 26,
      title: "Baamonde to Miraz",
      route: "Baamonde → Miraz",
      distance: "14.5km",
      region: "galicia",
      excerpt: "Doss day. UK volunteers run old priest house magnificently. Meditation request - 33% show up. Pierre must go.",
      content: `This is a doss day of 14.5 Km. Today the towns come up to meet me very fast. I get to the hostel quickly but am again beaten by the Yank. The hostel is the old house of the parish priest done up magnificantly and run by volunteers from the Uk. When checking in they said they hoped we would all come back for the meditation session this evening at 9pm. Norman came back for it 33% of us. He said it was great. I am lousy at that kind of thing.

It is nice to meet again some familiar faces. I met a Belgian today Pierre also. My friends told me last night to make sure to avoid him. He was weird they said -- he keeps asking inappropriate questions. If you are in conversation with him he adds irrelevant information to the conversation which makes you uncomfortable. If he is looking for accommodation he says there should be no more than five people in a dorm as more can spread diseases and he does not want any diseases given to him.`,
      image: "/camino/image7.jpeg"
    },
    {
      stage: 27,
      title: "Miraz to Sobrado",
      route: "Miraz → Sobrado",
      distance: "22.5km",
      region: "galicia",
      excerpt: "Beautiful monastery/hostel. Dorm has 120 beds. Uncontrollable old man. Music of the monks. Forest walking. Santiago just days away.",
      content: `There is an incredible monastery run by monks here. The dorm or dorms are in a building opposite -- 120 beds. I got a good bed -- I mean one I was happy with and a bottom bunk. 6 euros. The showers are magnificent - all brand new in a building beside the main building. There are three or four old guys all doing the walk. I am doing well by comparison. It is not uncommon to find them in some stop and they are staying behind because they are exhausted.

This morning I was having breakfast across the street from my Hostel. I was sitting near the door. Loud talk started happening in the cafe I looked around and it was Pierre being loud and inappropriate. Then I looked to my left and there he was passing the window on his way out and heading on the Camino. It was very early.

There was this old and I mean old man walking very dangerously. I got the feeling that some poor man would have to pick him up soon. He was all over the road like drunk unable to control his legs. I walked behind him hoping that the worse would not happen. I went out of sight I heard the fall I turned around and he was up on his legs.

Tonight we got the music of the monks for an hour. The forest walking is now really good beautiful. Santiago is now only days away.`,
      image: "/camino/image8.jpeg"
    },
    {
      stage: 28,
      title: "Sobrado to Arzua",
      route: "Sobrado → Arzua",
      distance: "21.5km",
      region: "galicia",
      excerpt: "Meet the real Santiago traffic. 600+ pilgrims per day in summer. Taxis everywhere. End of long peaceful walks. Days from Santiago.",
      content: `This is a place where a couple of thousand pilgrims could pass through on a daily basis. I suspect there are 600 people walking on it even in low season. I have being doing 24 to 45 km a day for a number of weeks -- it is hard not to look down on a little ---- but I try not to. This is the last few days for them ---- that is what the walk is for them unlike myself maybe 35days all in.

There are taxis every where willing to take your bag ahead of you. There are people that are walking the last few days only and you can feel the pressure to make sure to get the parchment. I suspect some of these peple have never walked more than a Km in their life.

Arzua is a real town. I have just come through nothing places ---- one bar or no bars no shops -- like rural Ireland in the 50s or 60s. Now I am buying my few supplies in an incredible super market. The town has every thing. I am staying in a hostel which has a restaurant on the ground floor. I am starting to meet old faces again --lots of them.`,
      image: "/camino/image10.jpeg"
    },
    {
      stage: 29,
      title: "Arzua to Santiago",
      route: "Arzua → Amenal → Santiago de Compostela",
      distance: "39km",
      region: "galicia",
      excerpt: "Final day. 39km to Santiago. City outskirts endless. Cathedral suddenly appears. Incredible journey complete. Parchment earned.",
      content: `LAST DAY. I left at 6.30am and there were several on the route already. I did the 39km great and got in around 1 o-clock. The 5 or so miles of the edge of the city are endless. You know you are approaching the cathedral but you do not know when you will see it. Then it kind of happens --- you are in a street and suddenly the cathedral is their.

Now the Camino rules state you must do a 100 Km in the last stages of the walk to get the parchment. You can do this in a week so therefore the last week we are all entitled to it. I however had to go to the Pilgrims office to establish that I had walked the entire Camino --- this is checked by the various stops one registers at. I walked to the pilgrims office which is on the edge of the city near the camino.

I discovered the Pilgrims office operates a queueing system -- you collect a number and you wait --- the wait can be anything from 1 to 3 hours I presume. My number was C 285 and it was serving c150 when I arrived. I went back to my hostel and got cleaned up showered and returned. I was processed quickly. I was told I was one of the very few to be walking the Camino Inlges the whole way. I walked into Santiago on day 34 having walked from Irun in Spain and having spent one full day in Gijon and walked for 33 days.`,
      image: "/camino/image1.jpeg"
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

      {/* Route Overview */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          <div className="p-8 md:p-12">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-blue-500 to-teal-600 rounded-2xl flex items-center justify-center text-white">
                <MapPin className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-3xl md:text-4xl font-black text-stone-900">The Route</h2>
                <p className="text-stone-600">Irun, Spain → Santiago de Compostela</p>
              </div>
            </div>

            {/* Route Highlights */}
            <div className="grid md:grid-cols-3 gap-6 mt-8">
              <div className="bg-blue-50 rounded-2xl p-6">
                <div className="text-blue-600 font-bold mb-2 text-sm uppercase tracking-wide">Start</div>
                <div className="text-xl font-bold text-stone-900">Irun</div>
                <div className="text-stone-600 text-sm">Basque Country, Spain</div>
                <div className="text-stone-500 text-xs mt-2">On the French border</div>
              </div>

              <div className="bg-teal-50 rounded-2xl p-6">
                <div className="text-teal-600 font-bold mb-2 text-sm uppercase tracking-wide">Route Type</div>
                <div className="text-xl font-bold text-stone-900">Coastal</div>
                <div className="text-stone-600 text-sm">Camino del Norte</div>
                <div className="text-stone-500 text-xs mt-2">Along Bay of Biscay</div>
              </div>

              <div className="text-cyan-50 rounded-2xl p-6">
                <div className="text-cyan-600 font-bold mb-2 text-sm uppercase tracking-wide">End</div>
                <div className="text-xl font-bold text-stone-900">Santiago</div>
                <div className="text-stone-600 text-sm">Galicia, Spain</div>
                <div className="text-stone-500 text-xs mt-2">817.5km total</div>
              </div>
            </div>

            {/* Visual Route Timeline */}
            <div className="mt-8 pt-8 border-t-2 border-stone-100">
              <h3 className="text-xl font-bold text-stone-900 mb-6">The 817.5km Coastal Journey</h3>

              {/* Route Flow */}
              <div className="relative">
                {/* Connecting Line */}
                <div className="absolute top-6 left-6 right-6 h-1 bg-gradient-to-r from-blue-500 via-teal-500 to-cyan-600 rounded-full" />

                {/* Stops */}
                <div className="relative grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { name: 'Irun', region: 'Start', km: '0' },
                    { name: 'San Sebastian', region: 'Basque Country', km: '27' },
                    { name: 'Bilbao', region: 'Basque Country', km: '160' },
                    { name: 'Castro-Urdiales', region: 'Cantabria', km: '200' },
                    { name: 'Santander', region: 'Cantabria', km: '280' },
                    { name: 'Gijon', region: 'Asturias', km: '450' },
                    { name: 'Ribadeo', region: 'Galicia', km: '650' },
                    { name: 'Santiago', region: 'End', km: '817' },
                  ].map((stop, idx) => (
                    <div key={idx} className="relative">
                      {/* Marker */}
                      <div className="relative z-10 w-12 h-12 rounded-full bg-white border-4 border-blue-500 mx-auto mb-3 flex items-center justify-center shadow-lg">
                        <span className="text-xs font-bold text-blue-600">{idx + 1}</span>
                      </div>
                      {/* Info */}
                      <div className="text-center">
                        <div className="font-bold text-stone-900 text-sm mb-1">{stop.name}</div>
                        <div className="text-stone-500 text-xs mb-1">{stop.region}</div>
                        <div className="inline-block bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                          {stop.km} km
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Route Stats */}
              <div className="grid md:grid-cols-3 gap-4 mt-8">
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-100">
                  <div className="text-blue-600 text-xs font-bold mb-1 uppercase">Stage 1</div>
                  <div className="font-bold text-stone-900">Irun → Bilbao</div>
                  <div className="text-stone-600 text-sm">Basque coastal highlands</div>
                </div>
                <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-xl p-4 border border-teal-100">
                  <div className="text-teal-600 text-xs font-bold mb-1 uppercase">Stage 2</div>
                  <div className="font-bold text-stone-900">Bilbao → Ribadeo</div>
                  <div className="text-stone-600 text-sm">Cantabria & Asturias coast</div>
                </div>
                <div className="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-xl p-4 border border-cyan-100">
                  <div className="text-cyan-600 text-xs font-bold mb-1 uppercase">Stage 3</div>
                  <div className="font-bold text-stone-900">Ribadeo → Santiago</div>
                  <div className="text-stone-600 text-sm">Through Galicia</div>
                </div>
              </div>
            </div>
          </div>
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
