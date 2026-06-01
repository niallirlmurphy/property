import React, { useState } from 'react';
import { MapPin, Calendar, ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DayEntry {
  day: number;
  title: string;
  distance?: string;
  content: string;
  image?: string;
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

  const expandAll = () => {
    const allDays = new Set(dayEntries.map(d => d.day));
    setExpandedDays(allDays);
  };

  const collapseAll = () => {
    setExpandedDays(new Set());
  };

  const dayEntries: DayEntry[] = [
    {
      day: 1,
      title: "Le Puy to Saint Private d'Allier",
      distance: "31.5km",
      content: `Le Puy with its Cathedral. Met Seamus's friend last night and had a good chat with him re everything French. The hostel was perfect, I headed off for 7 mass in the Cathedral — no mass. There were a few Germans present and they were ballistic. Headed off. The first 20 km is all uphill from 600 metres to 1100 metres and then you come down rapidly to my first overnight in Saint Private d Allier.

The day went fine one minor error — in France they mark the route going both ways to help walkers walking the opposite direction — a good idea but if you go in a bit of a loop off to see something then when you come back it is very easy to follow the signs in the wrong direction which I did. I met two walkers going the wrong way and then I noticed the sun was in the wrong place so I quickly adjusted.

I could hear the cuckoo — the donkey was crying out also. The Gite in the town was beautiful. There were three other Walkers, a guy from Nantes in France and a mother and daughter from Quebec. Dinner bed and breakfast was 28 euro. The guy from Nantes walked for a few months every year. After dinner at 8ish he was stretching himself getting ready for bed. I excused myself saying I needed a walk after dinner — the truth was there was a pub called Joyces in the town which needed investigation. It was very nice run by an English guy. I headed home at 10 and there was not a sound anywhere — lights out.`,
      image: "/camino/image5.jpeg"
    },
    {
      day: 2,
      title: "Saint Private d'Allier to Saugues",
      distance: "32km",
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
      content: `Got up and very confidently exchanged pleasantries with the girls. I felt half ok and headed off but I improved every half hour. That is not to say it was easy. We are in dog rough mountain territory all above 1000 metres rising to 1300 metres at one stage with the remnants of the snow still on the ground. The grass is white everywhere. No life in any village — coffee you must be joking.

Happy with day but still a half day behind. I book into the first Gite near the middle of the town 31 euro for dinner bed and breakfast. I am placed in this enormous room with about 14 beds — as it turned out I was the only occupant. I noticed there was a pub next door.

I joined a very nice Hungarian couple Joseph and Annie — about 30ish working in the secretariat in Brussels so we had a lot in common and had a great chat. They told me they were on a budget so when the nice lady came to pour the wine I said no thanks. When dinner was over 8.15 I slipped out for a pint — horror everyplace closed. I go back to the woman in the Gite and ask for a half bottle of red wine to bring to my room. She gives me a lovely jug of wine. I go to my room and my two sons have helped me with music downloads to my smart phone so Johnny Cash is selected and after a few glasses of wine I am almost waltzing to the music.`,
      image: "/camino/image7.jpeg"
    },
    {
      day: 4,
      title: "Saint Alban to Nasbinals",
      distance: "41km",
      content: `I set out today with the hope of doing an extra half stage to get back on track. I was helped a lot by the fact that Joseph and Annie were with me for 20 something km so that time passed very quickly. At one stage we met a school group and Joseph spoke to them and asked how far they were going and they politely asked us the same question.

The country again was dog rough at around 1000m. The state of organisation in the farmyards was below any standard in Ireland. There was a monster wolf in this part of the world over a hundred years ago and he killed over a hundred people mostly women and children. Today for the first day the rain came down also. I walked the last 20 km on the road as there was too much wild ups and downs in the forest.

I stay in a religious house tonight in Nasbinals. There is a lovely group of 6 elderly walkers that I have the chat with (they are from all over the world). One is Douglas who lives in Dorchester Avenue in Boston. It brought grand memories for me because as a student I worked on the buildings there for two summers. It is 12 euros for B and B tonight. I go down to the local hotel for a snack and a pint. The daffodils are in full display.`,
    },
    {
      day: 5,
      title: "Nasbinals to Saint Come d'Olt",
      distance: "32.5km",
      content: `Started in dense fog. Fields still white and no traffic on the roads but today we come down a bit in altitude and it is amazing that in the space of four hours walking we are into commercial farming and the traffic builds up as the milk collector goes around and the school bus etc.

I get a lovely hostel near the church (former prison). There is just a Dutch woman and myself. The only shop is at least a mile outside the village so I go and stock up with oranges. I leave the Gite at 6 o'clock in the evening to be in good time for grub and a drink. I discover too late for food — drink until 7 ok. The church was beautiful and coming out I met this lady and asked her about the shop. She really wanted to drive me to it.`,
    },
    {
      day: 6,
      title: "Saint Come d'Olt to Golinhac",
      distance: "33km",
      content: `I think I know it all now — Oopps. Morning beautiful and made great time and got to this beautiful town Estaing and had a coffee there. But things got a little confused. I climbed and climbed and climbed and realised there was a problem. Got to a farmers village on top of the hill. One farmer is by the door of his house. I show him the map and I ask him to point out ici (where this place is on map). This is too difficult for him so he brings me to the house next door because the man has a bit of English.

There was no knocking on the doors we just walked in. The second man was not satisfied without calling a third man in. They sit down and study my guide. They look like the local officers of the IFA in session. It is the middle of the day — break time and I think they are using me as an interesting distraction. Eventually the first farmer I met is detailed to bring me on a little journey to point out the route.

For the last 10 km I decide to stick to the road because the road does not go up and down as much as the forest paths. 2km on the road forks with no signs I go left. Doubts come into my mind. Normally I would always keep a bit of reserve water in the bottle as an insurance policy. Today the bottle is sucked dry before we finish. At 4.30 I saw this sign in the distance but could not make out the letters. It became Golinhac. I could have kissed it.`,
    },
    {
      day: 7,
      title: "Golinhac to Conques",
      distance: "21km",
      content: `Day not too bad. Meet up with two new Frenchmen on the route. Conques is one of those absolutely beautiful medieval villages in Lot valley. To enter it I had to descend for ever — a warning for tomorrow morning.

Went to the hostel all doors are open again and this time there are written instructions telling you what to do even to the extent of filling out a booking form and putting it in an envelope with the 14 euro and then putting it in a box. There are three of us only in the hostel: Stephano, the Dutch woman and myself.

There is a beautiful Cathedral that I visit. It is Good Friday and they are preparing for a procession through town. I join in. Stephano arrives back in hostel with a bag full of food and cans of beer which he insists on sharing with me. They have this black pudding specialty — it is like chewing plastic. It is Stephano's last night so we exchange phone numbers as he says he will come to Ireland.`,
      image: "/camino/image1.jpeg"
    },
    {
      day: 8,
      title: "Conques to Livinhoc-le-haut",
      distance: "23.5km",
      content: `Last night looking at those mountains towering over Conques in every direction you knew you had to get over them in the morning but they were so steep if in another circumstance someone said would you climb those for a bet of 100 euros you would just laugh but climb we did.

Gean from Nantes is with me. We stop at a tiny church (ten seats) half way up and even Gean is pumping sweat and takes a break. It is like climbing a never ending ladder. I move on ahead of Gean as I want to get the effort over. I get into town and Gean is in front of me — he has a better map than me and he has taken some short cuts. Livinhoc was deader than dead and should be left so. To add to the Uaigneas (lonesomeness) it rained also.`,
      image: "/camino/image4.jpeg"
    },
    {
      day: 9,
      title: "Livinhoc to Figeac",
      distance: "24.5km",
      content: `Figeac is a decent size town so I am looking forward to this. We are back into more commercial farms now. Arrived in town at 1 pm. Took me a little while to find a Gite. Doors open again but nobody at home. I find the phone number and ring and there is no problem except a caution on fleas. We are not to put our bags on beds.

We got a great evening meal. I found this nice pub for a pint. There is a girl of about twenty in charge of the pub and nobody else. At one stage she explained she needed to do something and she must have been gone 15/20 minutes with nobody inside the counter. This is probably all minimum wage territory.`,
    },
    {
      day: 10,
      title: "Figeac to Cajarc",
      distance: "31km",
      content: `I have a sore left foot a legacy of the first Sunday so I try and give it a break any chance I get so today is bank holiday with little traffic so I decide to get up early and take the direct route by road. I go hard and arrive at hostel at 12.30. They were cleaning the place. Last night there was a rock concert in town.

I explain to the guy that I want a bed. At first because it is so early he thinks I am part of the brigade from the night before who has not gone to bed yet. Quickly we rectify the understanding and get on like a house on fire. It is a lovely hostel. Gean arrives. Today he is definitely not happy with this Irishman. He said he started early and came very fast and wondered how I could be in front of him — tough.`,
    },
    {
      day: 11,
      title: "Cajarc to Varaire",
      distance: "24.5km",
      content: `Between Cajarc and Cahors was a major problem for me. I swallow my pride and go to Gean the professional mountaineer. He has in his guide one place just off the track in a place called Varaire called Marronniers and Gean phones and books me in.

During the walk the heavens opened and there were hailstones the likes of which I have never seen. I arrived at this outpost with nothing much except this pub named Marronniers and a Gite sign. The Director comes out to me. His appearances would fit in much better with the clientele at Ballinasloe horse fair in Ireland than they would with being a Director. He had this cute look. He walks straight in opens bedroom doors and one bed is available.

It was a group with mental issues. The guy invites me to join them for a snack. I am saluting and shaking hands with them for ever. The floors everywhere were just covered in water. The evening meal is ok but the Director being a cute whore saved a bit on the main course — boiled chicken (hen).`,
    },
    {
      day: 12,
      title: "Varaire to Cahors",
      distance: "39km",
      content: `Up early and walked hard. Met a very nice man from Friesland and walked the last 20 km with him. He was about 70 and was part of the group of 6 that I met way back in Nasbinals. Now my friend from Friesland peeled off as he felt he could do 30/40 km per day like me. He left his wife by agreement with the other group. He is a retired teacher.

I am going over the beautiful bridge into Cahors and this woman in a kiosk on the other side is shouting at me to come over. She is a volunteer in Cahors to help pilgrims. She gives me tea and biscuits and she suggests a gite run by an English lady. I quickly find the Gite up this maze of very narrow streets. The Gite name is Papillion Vert (the green butterfly) run by a charming English lady called Jackie.

I think it will not serve much purpose for me to start dividing one or two of those days. The best option is to take out one day rest now in Cahors and give my foot a break. The town has everything going for it and Jackie has a computer for me also. The mountains are beautiful but god you need to be back in civilisation every so often.`,
      image: "/camino/image2.jpeg"
    },
    {
      day: 13,
      title: "Rest Day in Cahors",
      content: `Break time. Dinner with Olivia a French garsun and Jackie. Jackie being cute said John can you cook and John being stupid says yes. So Jackie says all the materials are there so maybe you could make an Irish stew this evening. It turned out ok. At least it was all eaten.

I go to this bar for a drink. It turned out to be a French/Algerian bar. I leave my drink and walk to window to look out. Then I noticed a drunk coming back from the toilet mistakenly picked up my drink. I left a shout at him and the barman sorts everything out. Next drink I put 5 euros on the counter and the barman puts the drink on top of the note. That is a signal that it is free.

People go to the bar here for a social occasion. Guys are coming in and getting a shake hands or kisses (two here) from the barman. People are talking across tables — It is all a big social occasion.`,
    },
    {
      day: 14,
      title: "Cahors to Montcuq",
      distance: "33km",
      content: `Fields getting a bit bigger now and farmers living in their chateaus each with their own name. I make no navigation mistakes now so it is getting boring. I meet a lady in town and she asks me if I want anything: I say the local Gite. She points the way and as it turned out she was the woman of the house in the Gite — cute woman.

It was an enormous Gite with just three of us staying that night. The husband was walking up and down outside the door to welcome any arrivals. He could not be more helpful and all for 30 euros dinner bed and breakfast. Went down to the town that evening and it was lively. I found an English bar and met some English people living locally.

I have a long journey tomorrow so I am trying to cut a bit off it looking for a more direct route for part of the way. I ask the barman about walking to Moissac. He just cannot believe it saying you cannot walk to Moissac. It is impossible. This guy is a bar man in a bar on the walking route.`,
      image: "/camino/image6.jpeg"
    },
    {
      day: 15,
      title: "Montcuq to Moissac",
      distance: "38.5km",
      content: `I felt the long walk today. Some of the walk was in ferocious scrub territory. No human being anywhere. The climb was so steep at one short length over rocks that ropes were in place to pull yourself up. Then you come to the outskirts of Moissac and you think you are there but like all big cities an hour later I am still walking.

I head for the convent on the hill near the Cathedral. It is run by volunteers which is great but volunteers need to be managed. This guy in charge asks for name I say John, Mr John. He starts to look at his list of reservations. I say no reservation. He says no reservation and drops the list and looks at me. I felt like saying — no reservation like Mary and Joseph going to Bethlehem.

Dinner time came and there was buckets of soup to start. Later the big man gave out hymn sheets and we sang hymns for a few minutes. I visit the Cathedral which is beautiful and the town is beautiful but I need to conserve the energy so I go to bed early.`,
      image: "/camino/image8.jpeg"
    },
    {
      day: 16,
      title: "Moissac to Miradoux",
      distance: "36km",
      content: `We are down from the high mountains now and you can smell the riches. The farmers are again all making statements with their big Chateaus. We are in vineyard country. Farms are big in size also. This morning I got a mighty break in that the first 8 miles was on a canal bank so very flat.

I intended stopping in Saint Antoine but it looked so lonesome it frightened me. When I hit town I went in to the first hostel. Therese was the woman's name. She was well into her 70's with about six layers of clothes around her. There was this enormous table in the kitchen stacked high with all kinds of food. She gave me a beer and set about stuffing papers into my boots to dry them.

The dinner went on for three hours — there was beer, wine and Liqueur to finish off. The kitchen was totally devoted to the walk. Every spare corner had a crucifix or a religious picture or messages from people who had stayed. There was no tv. She had a record player and she played English, French and Italian music for me. Once she got up to do a little waltz around the table. I enquire how much. She pointed to an old jar saying it is voluntary.`,
    },
    {
      day: 17,
      title: "Miradoux to La Romieu",
      distance: "34km",
      content: `Therese had a mighty breakfast for me and afterwards she was out in the road waving goodbye to me. In route there was this beautiful cathedral in Lectoure which I visited and said prayers for all. I met a lovely tall young Dutch guy. He had injured his leg and was out of the Camino waiting for his father to collect him.

Got there no problem. Wild enough weather. Could not find hostel. Tourist office open and she points out building to me (it had no sign and was as many are a former convent). A lovely guy in charge and he gives me all the options. I opt for a single room tonight for 30 euros.

I decide to get my own grub this evening and go into a bread shop. I ask where can I get a butcher shop. She says Condom which is 16 km away. I say to her you want me to walk to Condom for meat — she gets the message and laughs. The best I could get together was six frankfurters from another tiny shop and a tin of peas.`,
    },
    {
      day: 18,
      title: "La Romieu to Montreal du Gers",
      distance: "33km",
      content: `Making big progress long journeys every day. Warden this morning said forecast bad ie rain in afternoon. I am first into breakfast so I am ready to go like mad at 7ish. Hit my town with no rain at around 2pm. Left knee giving trouble but it will sort out.

I visited in route one of the oldest churches in the region Eglise de Routges. There is a small door on the side of the church and this was for "the Cagots" — these were an outcast group of people of uncertain origin. They lived segregated lives and were believed to have leprosy, syphilitic, unclean and bearers of all types of evil so they had a separate door to enter the church.

Arrived in town. Found the tourist office on Main Square next to Church. Very helpful girl offered to phone Gite just off the square. Anita originally from the Black Forest in Germany owns it and she speaks good English. It is a lovely quaint place with the old beams and all the facilities you could need. The food that evening was the best so far and down came the rain.`,
    },
    {
      day: 19,
      title: "Montreal du Gers to Nogaro",
      distance: "36km",
      content: `Good days walking. Until now I only meet two people briefly who had English as their first language. It is all about to change. I arrive at this communal hostel. I am placed in this big round room of beds. In the middle of the room there is a big table with three guys drinking wine.

The three at the table give me the nod. I join them. We go to a beautiful local shop and get buckets of fish bread and wine and go back to the gite and have a big big meal. It was a nice night. The three at the table were Philippe from Basque country, Conrad the Doc. from Canada, and Geert from Holland.

They were great company and we had buckets of stories and wine and beer to match. The language was split between French and English. Philippe was 67 but looked 55. Geert had those rambling roguish eyes. He was into music and singing. Philippe was retired from the Department of youth and sport. Conrad was a general medical practitioner in Canada. All health services are free in Canada including your visit to the GP.`,
    },
    {
      day: 20,
      title: "Nogaro to Aire-sur-L'Adour",
      distance: "35.5km",
      content: `Walked on my own today. So easy to follow the system. There was rain and muck everywhere. So there was nothing for it except head down and go like the hammers of hell. These last few days I got startled a few times as French fighter planes flew in low formation overhead.

Today also the clouds lifted for a minute and I got my first glimpse of the Pyrenees — a long long row of stacks capped in white. Found this hostel run by a lovely lady. She took infinite time explaining everything to me. I got a few cans and two chops and bread and had great meal.

The husband of the lady took over responsibility and remained in charge until after 10ish. These people are up at 6ish. There were four of us staying so they got something like 50 euros in total from us.`,
    },
    {
      day: 21,
      title: "Aire-sur-L'Adour to Arzacq-Arraziguet",
      distance: "35km",
      content: `Everywhere so far there are religious symbols including in this house. The crossroads often has a ten foot cross erected. All the middle class houses have a five foot fence encircling everything with these two giant dogs like Alsatians. There is a sign in every house "beware of chien (dog)".

Today we are in a big valley. The fields some days were 20 to 30 acres in the valley. Today we have cornfields going from 100 acres up to 600 acres. A square mile of land is 640 acres so you should know how long it takes to walk a mile and then do your calculation.

I book into this beautiful gite communal and who is there except the Doc, the Basque and the Dutch man. There are two more Canadians and one Canadian a guy called Paul invited me down to the pub for a drink. It is very easy to have a party. You just find a reason and go across the road to the shop and get a bottle of wine for three euros. Philippe the Basque specialised in this dried black pudding which we eat as is and it was lovely but really tough.`,
    },
    {
      day: 22,
      title: "Arzacq-Arraziguet to Arthez-de-Bearn",
      distance: "29km",
      content: `I am going very ahead of schedule. A hard days slog in the rain and muck. Met Martina from Germany. Met Latvian lady that I had not met for some time and walked for a spell with four french men about my age all with the same capes so you could pick them out a mile away.

I was first in town and went to the hostel. All the usual suspects are present and we vote for the delivered meal. We have a great evening with a few parties. There is a guy Michael from Southampton also 48 years of age who quit his job with the BBC to do the walk.

A man calls with the food delivery. He has this big trolley and first he takes out this big pot of boiling soup, followed by salad and main course of duck and dessert and two bottles of wine for six people all for 11 euros each.`,
    },
    {
      day: 23,
      title: "Arthez-de-Bearn to Navarrenx",
      distance: "29km",
      content: `I am with the usual gang and that helps. Today there is a sign in the hostel saying to register today you must go down to Mrs Murphy's bar in whatever street. There is one restaurant open for grub.

When we go down to the pub to register the woman's husband has been out somewhere with his wellington boots and he walks in the door before us and leaves a trail of muck. The wife goes wild pointing at the trail. He sheepishly shrugs his shoulders.

The woman tells us there is no place else in town open and there will be no place open tomorrow morning (Monday). The best she will be able to do is give us a coffee in the morning. We eat in the only restaurant and get an indifferent service from a 20ish male.`,
    },
    {
      day: 24,
      title: "Navarrenx to Uhart-Mixe",
      distance: "37km",
      content: `We wanted to reach the bottom of the Pyrenees in two days but finding accommodation in the right place to split the journey was the issue. We opted to go off the beaten track and book a gite called gite Lescargot in Uhart-Mixe.

Usually during the day we split up and walk at our own pace. Normally I would walk non stop. My supplies were a pint of milk to be drank 10 to 12ish. An orange at 1ish and a mars bar 5km from the end. I was gone another 10km and there was a factory on the side of the road making pate and they erected a little shelter on the path with a seat and there were tins of pate and you put two euros donation in a box. Had a great feed.

We arrive at our Gite. There is this beautiful husband and wife team of about 60. First we are put sitting down in front of this big log fire burning like mad. They give us lemon drink and cannot be more helpful. We got four massive courses with as much wine as was needed. The meal finished with a liqueur and a beer for myself. This was heaven because day after day we had to stuff the feet into wet boots.`,
    },
    {
      day: 25,
      title: "Uhart-Mixe to Saint-Jean-Pied-de-Port",
      distance: "28km",
      content: `The breakfast again was a mighty affair of food. That man with the lovely smile stood there next to the table urging another bit of bread: try the honey; what about a bit of cheese. We were charged 30 euros each for all that drink included. When breakfast was over we started in the rain and the man accompanied us with an umbrella to make sure we got on the right path. It is lovely to meet nice people like that.

In route today we come across this kid goat with his head all caught up in a fence and he is crying like a baby. I get him untangled but not before losing some skin off my knuckle which Doc sorted out with his ointment treatment.

We arrive in town and there is this incredible buzz. This is the start of going over the Pyrenees and it is a very popular starting point as the airports are nearby. This evening there is super news — the guy says the high route is ok. Every face is alive and happy. There is this great feeling. If this was an easy cake walk nobody would want to do it. They are all here for the challenge.`,
    },
    {
      day: 26,
      title: "Saint-Jean-Pied-de-Port to Roncesvalles (Spain)",
      distance: "24.8km",
      content: `Woke a few times during night to horror of hearing high wind. We go outside and the street signs are banging and who comes along the street but the man giving advice. It was very simple: high winds go the low route. I put my head down and said nothing and went in front. As it turned out the vast majority opted for the high route. The wind was fierce.

We reach our first challenge at a curve in the path. About eight of us lie down anywhere that is half comfortable because the power of the wind is too strong. Along comes Conrad the Doc. I am delighted to see him because you can take turns walking in each others slip stream to get some relief from the wind.

It feels impossible at times as you raise your foot and the wind pushes you back and your foot lands in the same place or you stumble sideways. At one stage I was behind Conrad and desperately needed a break. Every step helped. Then you come to this part in the top of a mountain that is a real bummer — You go over the peak and down but then back up again.

We find the path is closed off because of snow drifts. I end up face down in a snow embankment. I jump up and end up being flung against the embankment. I jump up again and am really rolled around on the embankment. This time I surrender and slowly pull myself up to a half sitting position. My walking stick has doubled in two.

Down come three poor guys walking with their bikes. They were holding their bikes sideways using the wheels as brakes as the wind was catching the panniers. Then suddenly they were hit. All three ended up in an exposed embankment on the other side of the path lying on the ground. There was no panic. On the contrary most of us looked on the funny side of it.

In terms of energy drain it certainly was one of the hardest days I endured but I am glad I did it. Quite a few turned back and got taxis.`,
      image: "/camino/image9.jpeg"
    },
    {
      day: 27,
      title: "Roncesvalles to Zubiri",
      distance: "22km",
      content: `There were a few people having Pyrenees nightmares over night but I slept through it all. This day was a cake walk compared with yesterday. Stayed in a very good private hostel. We went to this restaurant and had a great lunch.

I was in the bed next to a very nice girl from Derry called Sullivan who works for Concern together with her husband a man called Power from Waterford. If you think you are good on the trail able to walk fast and do 40km some days then spare a moment for this lady who is doing two stages everyday ie 50 km plus per day.

I slip out for a pint after dinner. Normally we were in bed shortly after 9 with all lights out before 10 pm. I come back shortly after 10pm and the whole place is in total darkness. I gingerly go to where I think the bed is and make advances to get in to be repelled strongly by a big man. Luckily my Basque friend has realised I have a problem and he points a torch at my bed.`,
    },
    {
      day: 28,
      title: "Zubiri to Pamplona",
      distance: "22km",
      content: `Still wet and muddy but another cake walk so I split with my two friends in Pamplona as they go on. That is the not nice part of the whole thing. I had become good friends with Conrad the Doc. and Philippe the Basque. We understood each other and went our own way at times to be alone but the company was very good and I spent two great weeks with them.

The three weeks prior to that were testing as several days I walked 35 plus km without seeing more than one or two walkers and in all this time when there was company it was invariably with non English speaking or individuals with very little English.

I noticed a young guy following us so I went back and introduced myself. He was Heiko from Hamburg. He liked our pace so I brought him into the company. He was a fine guy that worked as an aircraft mechanic.

I go to this nice American on the trail for the past few days and he speaks very very loud. His name is Todd and he is from corn country in North Dakota. He is walking with this 75 year old man from Bavaria called Norbert. We agree to meet that night in a restaurant that gives a special deal to pilgrims and boy do we have a good nights craic.

I think the cafe and pub culture in Spain and France is very healthy. The owner of the bar or cafe is quite happy to have two people there for an hour. This morning Sunday the little cafes were full of people having their croissant and coffee. It is a big social occasion.`,
      image: "/camino/image10.jpeg"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 via-white to-stone-50">
      {/* Hero Section */}
      <div className="relative h-[60vh] overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url(/camino/image9.jpeg)`,
            filter: 'brightness(0.7)'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/20 to-black/60" />

        <div className="relative h-full flex flex-col justify-end pb-12 px-4 max-w-6xl mx-auto">
          <Link
            to="/"
            className="absolute top-6 left-4 flex items-center gap-2 text-white/90 hover:text-white transition-colors bg-black/30 backdrop-blur-sm px-4 py-2 rounded-full"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>

          <h1 className="text-5xl md:text-7xl font-bold text-white mb-4">
            Walking the Camino
          </h1>
          <p className="text-xl md:text-2xl text-white/90 max-w-3xl mb-6">
            A journey through France and Spain on the ancient pilgrimage route from Le Puy to Pamplona
          </p>
          <div className="flex flex-wrap gap-6 text-white/80">
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              <span>Le Puy → Pamplona</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              <span>March - April 2012</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">28 Days</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">~850km</span>
            </div>
          </div>
        </div>
      </div>

      {/* Introduction */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="prose prose-lg max-w-none">
          <p className="text-xl leading-relaxed text-gray-700">
            The following was my planned itinerary for the walk from Le Puy in France (just south of Lyon) to Pamplona.
            It was a little ambitious — lengths more than recommended so I allowed a few extra days for this and for
            eventualities like bad weather. It starts in the Massif Central — a high barren volcanic region and goes
            south entering the lovely Lot valley — then over the Midi Pyrenees — then over the Pyrenees and then west
            to Pamplona.
          </p>
        </div>

        {/* Controls */}
        <div className="flex gap-4 mt-8 mb-6">
          <button
            onClick={expandAll}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors flex items-center gap-2"
          >
            <ChevronDown className="w-4 h-4" />
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-4 py-2 bg-stone-600 text-white rounded-lg hover:bg-stone-700 transition-colors flex items-center gap-2"
          >
            <ChevronUp className="w-4 h-4" />
            Collapse All
          </button>
        </div>

        {/* Day Entries */}
        <div className="space-y-4">
          {dayEntries.map((entry) => (
            <div
              key={entry.day}
              className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* Header */}
              <button
                onClick={() => toggleDay(entry.day)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-stone-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex-shrink-0 w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-bold text-lg">
                    {entry.day}
                  </div>
                  <div className="text-left">
                    <h3 className="text-xl font-semibold text-gray-900">{entry.title}</h3>
                    {entry.distance && (
                      <p className="text-sm text-gray-600">{entry.distance}</p>
                    )}
                  </div>
                </div>
                <div className={`transition-transform ${expandedDays.has(entry.day) ? 'rotate-180' : ''}`}>
                  <ChevronDown className="w-6 h-6 text-gray-400" />
                </div>
              </button>

              {/* Content */}
              {expandedDays.has(entry.day) && (
                <div className="px-6 pb-6">
                  {entry.image && (
                    <img
                      src={entry.image}
                      alt={entry.title}
                      className="w-full h-64 object-cover rounded-lg mb-4"
                    />
                  )}
                  <div className="prose prose-stone max-w-none">
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

        {/* Conclusion */}
        <div className="mt-12 p-8 bg-gradient-to-r from-amber-100 to-orange-100 rounded-xl">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Journey Complete</h2>
          <p className="text-lg text-gray-700 leading-relaxed">
            That completes stages 1 and 2 of the trail of St. James from Le Puy in France to Santiago —
            almost 1,000 miles. Stage 2 in 2008 and Stage 1 in 2012. It was lovely and thanks to everyone
            that helped.
          </p>
        </div>

        {/* Getting Back Section */}
        <div className="mt-8 p-6 bg-blue-50 rounded-xl border border-blue-200">
          <h3 className="text-xl font-semibold text-gray-900 mb-3">Getting Back to Dublin from Pamplona</h3>
          <p className="text-gray-700 mb-4">
            You need to get a bus from Pamplona to Bilbao and fly out from Bilbao. Bus costs around 17 euros
            and takes over two hours. Buy the ticket as early as you can to avoid the possibility of the bus
            being booked out.
          </p>
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">Bus Timetable (La Burundesa)</h4>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-gray-700 mb-1">Mon-Sat:</p>
                <p className="text-gray-600">7:00, 10:00, 13:00, 15:30, 18:00, 20:30</p>
              </div>
              <div>
                <p className="font-medium text-gray-700 mb-1">Sun & Bank Holidays:</p>
                <p className="text-gray-600">9:00, 11:15, 16:00, 17:30, 20:00</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mt-3">
              From Pamplona central bus station at Park Castillo (underground). Airport bus from Bilbao
              costs less than 2 euros compared with 25 euros plus for a taxi.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-stone-900 text-white py-8 mt-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-stone-400">
            A personal travel diary documenting the ancient pilgrimage route
          </p>
        </div>
      </footer>
    </div>
  );
};

export default CaminoPage;
