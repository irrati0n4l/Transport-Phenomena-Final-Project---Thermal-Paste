### Intro
00:00:00,320 --> 00:01:07,800 [Pranav]
Hey, everyone. Imagine this, you're an hour long into a render, and without any warning, the frame rate just drops. Nothing has crashed. The processor has simply decided to run slower because the heat could not leave the chip fast enough. This is called thermal throttling, and one of its quietest culprits is a layer you can barely see, a film of thermal paste only a few micrometers thick. I am Pranav, and I've built the Newtonian simulator, which is called the Paste Squeeze Lab. Our project asks a precise question about that film. When a cooler is clamped on with a steady force, how thick does the paste layer end up? How long does it take to get there? And how many degrees does that thickness cost? To answer it, we've built two independent components. The first is a basic Newtonian squeeze flow simulator, and, uh, which you'll see, running live soon. The second is an analytical and numerical study of the non-idealities, which is the non-Newtonian pastes, which include power law and Bingham flow on an example of a 700-watt AI GPU. 

00:01:10,800 --> 00:01:47,960 [Yaswitha]
I am Yaswita, and I cover the general theory and the application-specific equations, the lubrication reduction, dimension analysis, and the GPU thermal model. Everything we use comes from the three lecture decks of the Transport Phenomena course, like conservation and transport equations, momentum, energy and fluid flow, and dimensionless numbers as ratios of physical effects. And mass, momentum, energy balances are the same for every paste. Here, the-- only the stress law changes. Our two components are a Newton closure and ones with power law and Bingham closures. 

00:01:52,340 --> 00:02:06,680 [Avanika]
Hello, guys. This is Avanika, and I have worked on the non-Newtonian model, which mainly focuses on the power law and the Bingham models, and does verification to, to a suite which runs over 20 tests to verify whether the physics are followed with the assumptions. 

00:02:08,199 --> 00:02:22,380 [Avanika]
Now, uh, moving on to, like, what, uh, brings in... So what else, what else we modeling using this non-Newtonian is that any real-life, uh, GPU with, like, a 700 watt, as we're seeing in this hardware benchmark, would require a 

00:02:23,460 --> 00:02:55,280 [Avanika]
constant wa- would, uh, would be where, uh, we are analyzing under a constant volume, uh, and we are verifying it over, uh, various theorems such as Reynolds theorem. And we are also verifying that the lubrication of the creeping flow assumptions hold via the dimensionless groups, such as the aspect ratio and the Reynolds number. And we're coupling it with the resulting gap, which varies over time, which was the bond line thickness as well as the, uh, radius of coverage. And we're also integrating the Fourier heat conduction to quantify the exact, uh, temperature change in the 700-watt GPU.

### Section 1
00:00:00,520 --> 00:00:04,400 [Yaswitha]
Let's talk about the physical picture of the squeeze flow of thermal paste. 

00:00:06,040 --> 00:00:21,500 [Yaswitha]
What's actually happening physically inside a computer? Heat is generated in the silicon die. From there, it has to travel through a thin layer of thermal paste, pass into the metal lid or cold plate, spread out through a heat sink, and finally escape into the moving air. 

00:00:23,220 --> 00:00:28,200 [Yaswitha]
Now, the easiest way to, to think about this path is like a chain of resistors in series. 

00:00:29,300 --> 00:00:37,800 [Yaswitha]
Each layer puts up a little bit of resistance to the heat, which means all of those individual temperature drops simply add up. 

00:00:40,820 --> 00:00:54,240 [Yaswitha]
The thermal paste is the odd one out. Even though it's 10 to 100 times thinner than all the other layers, it's a terrible conductor by comparison. It only conducts about 5 watt per meter kelvin, 

00:00:55,820 --> 00:01:01,560 [Yaswitha]
whereas the copper sitting right next to it conducts roughly 400 watt per meter kelvin. 

00:01:02,960 --> 00:01:12,580 [Yaswitha]
Because of that huge gap in conductivity, thickness immediately turns into thermal resistance. On a standard 20 by 20 millimeter die, 

00:01:14,240 --> 00:01:20,440 [Yaswitha]
every extra 20 micrometers of paste costs about 100th of a kelvin per watt. 

00:01:22,760 --> 00:01:26,300 [Yaswitha]
At 100 watt, that is 1 kelvin 

00:01:27,600 --> 00:01:29,720 [Yaswitha]
 at 20 micrometers 

00:01:30,900 --> 00:01:47,380 [Yaswitha]
and 10 kelvin at 200 micrometers. For our hardware benchmark, rather than choosing any arbitrary benchmark, we choose the H100 class GPU of 700 watts on an 814 square millimeter square die, 

00:01:49,520 --> 00:02:10,360 [Yaswitha]
and the heat flux is 86 watts per second, watts per centimeter square.  At that level of intensity, there is zero margin for error, so every single micrometer matters. So how do we actually predict how thin we can squeeze this paste? 

00:02:11,460 --> 00:02:14,880 [Yaswitha]
So to answer that, we need a small analytical toolkit .

00:02:16,500 --> 00:02:22,000 [Yaswitha]
The first is the dimensions. Everything in physics is built out of mass, length, and time. 

00:02:23,220 --> 00:02:32,780 [Yaswitha]
Making a habit of, like, checking that every term in an equation shares the same dimensions is the fastest way to catch any algebra slips. 

00:02:35,680 --> 00:02:54,960 [Yaswitha]
Second, the force scales. When a fluid moves, two main forces are competing. One is inertia, the fluid's tendency to keep moving, scales as rho U square L square. Meanwhile, viscous drag, the fluid's internal friction, scales as mu UL. 

00:02:57,700 --> 00:03:13,120 [Yaswitha]
And the ratio of this inertia scale and the viscous scale is the Reynolds number. It can be read as a ratio of two times, like how long viscosity takes to spread momentum across the layer divided by how long the flow takes to carry fluid across it. 

00:03:14,740 --> 00:03:28,920 [Yaswitha]
Applying that directly to our squeeze film, here the length scale that really controls viscous friction is the tiny gap height, which is h. So our squeeze film Reynolds number becomes 

00:03:30,440 --> 00:03:32,000 [Yaswitha]
rho WH by mu. 

00:03:34,960 --> 00:03:53,800 [Yaswitha]
With a density of 2,500 kilograms per cubic meter, a slow squeeze speed of 10 micrometers per second, a gap of 50 micrometers, and a thick viscosity of 100 Pascal-second, we roughly get the Reynolds number as 10 to the power minus 11. 

00:03:56,720 --> 00:03:59,480 [Yaswitha]
Since the Reynolds number is so tiny, 

00:04:00,560 --> 00:04:11,720 [Yaswitha]
it tells us that inertia is completely irrelevant here. There is no splashing, no turbulence. The paste  just creeps outward like cold honey in slow motion. 

00:04:13,400 --> 00:04:27,640 [Yaswitha]
That brings us to our third tool, the control volume and the Reynolds transport theorem. Like, imagine slicing out an imaginary cylindrical column of paste of radius R and height as a function of time. 

00:04:29,240 --> 00:04:58,320 [Yaswitha]
As the top plate presses down at speed W, the column gets squeezed and loses volume at a rate of pi R square W. Since the paste has constant density, it can't just compress and vanish. All of the displaced volume has to escape sideways through the outer rim of the cylinder. Dividing by the circumference gives us the radial volume flux per unit circumference, Q is equal to RW by 2. 

00:04:59,700 --> 00:05:04,940 [Yaswitha]
Or if you write it in general Cartesian form, it's simply grad dot Q is equal to U, 

00:05:06,320 --> 00:05:10,640 [Yaswitha]
and it holds identically for every paste rheology. 

00:05:12,780 --> 00:06:00,020 [Yaswitha]
Coming to the thin gap simplification, this is where the shape of the gap gives us a huge mathematical break. The, the thinness ratio, the epsilon, the gap height divided by the plate radius is tiny, that is around 10 to the power minus 3. So when we compare every term in the full momentum equation using that small number, things simplify dramatically. Because the paste is squeezed through such a narrow slit, the sideways radial speed ends up much larger than the downward plate speed, specifically by a factor of 1 by epsilon. That also means the shearing of the fluid is completely dominated by how fast the radial velocity changes vertically across the gap. 

00:06:02,480 --> 00:06:10,300 [Yaswitha]
As a result, both inertia and the horizontal viscous terms just drop right out. Even better, pressure doesn't have 

00:06:12,260 --> 00:06:17,700 [Yaswitha]
to vary across such a thin gap, so pressure only depends on the radial position R. 

00:06:18,940 --> 00:06:28,860 [Yaswitha]
So everything collapses down to a clean local slit flow balance, that is 0 is equal to minus DP by DR plus dou TRZ by dou Z. 

00:06:30,800 --> 00:06:47,320 [Yaswitha]
Integrating across the gap with symmetry about the mid-plane gives a result we will reuse for all three pastes. The shear stress is linear across the gap, tau equals minus G times zeta, where G is the radial pressure gradient. 

00:06:49,540 --> 00:07:07,540 [Yaswitha]
And we haven't even picked a specific material yet. No viscosity model, no yield stress, and, uh, still we already know the exact shape of the stress field. Conservation laws alone handed us both the continuity flux and this linear stress profile.

### Section 2
00:00:01,420 --> 00:01:16,120 [Pranav]
Let's start simple. Closure number one, let's go with the Newton's law of viscosity, tau equal to mu du by dz, where mu is the, Newtonian viscosity, which is, as a default, 100 Pascal-second. We can integrate this with the no-slip, no-slip condition at both planes, which gives us a par-parabolic velocity profile of gz h minus z divided by 2 mu. Now, we can get the flux by integrating this between the plates, and we get a flux value of gh cubed divided by 12 mu. We can equate the flux with, rw by 2, and, then we can get an equation for the pressure gradient g, where-- which we get as, 6 mu wr over h cubed. We can integrate, the pressure gradient from the free edge, uh, and, uh, get a value of the pressure as a function of radius. And this will get, uh, p equal to 3, 3 mu w over, h cubed times r squared minus r squared. 

00:01:19,900 --> 00:01:48,700 [Pranav]
Integrating the pressure over the whole disc gives us the Stefan's law, f equal to 3 pi mu wr to the fourth over 2h cubed. Two consequences here are actually worth remembering because, for our given clamp and our die geometry, we see that, the peak is exactly twice the mean, which is 62.5 at the center, versus 31.25 as the mean. 

00:01:49,740 --> 00:02:08,120 [Pranav]
And, uh, the second is that force is-- force rises as 1 over h cubed or, an inverse cubic law. So halving the gap makes the squeeze eight times harder. This is why squeezing slows down so brutally. Now to turn this into a gap versus time law. 

00:02:14,020 --> 00:02:33,820 [Pranav]
Under a constant clamp force f, Stefan's law becomes an ordinary differential equation for the gap. For a paste that already fills a disc of radius r, it's the-- it separates immediately. 1 by h squared equals 1 by h0 squared plus 4 times ft divided by 3 pi mu r to the fourth. 

00:02:35,980 --> 00:02:44,160 [Pranav]
At later times, h falls as t to the minus one-half, and a Newtonian paste actually never reaches a resting thickness. 

00:02:45,840 --> 00:03:43,000 [Pranav]
But a real pea-sized dot does not fill the whole disc. Its volume is conserved, so r squared equal to v over pi times h, and the radius grows as the gap shrinks. Su-substituting that into the Stefan's law, the force now scales as h to the minus 5, and the gap law becomes h to the minus 4 equal to 1 by h at 0 to the power 4 plus 8 pi ft divided by 3 mu v squared. So h falls like t to the minus one-quarter here. When the blob reaches the die edge, at the cap thickness, h critical equals v over the die area. Then the radius is pinned. The slope changes from, uh, minus 5 to minus 3 in the force, and the late-time law returns to t to the minus one-half. Our GPU benchmark has h critical equal to 61.4 micrometers. 

00:03:50,520 --> 00:04:16,240 [Pranav]
Two scaling checks tie this together. Buckingham's theorem is one of them. Five variables, three base dimensions, which gives us two dimensionless groups, and the exact solution which fixes big pi, fh cubed over mu ur to the fourth at 3 pi over 2. And the second one is similarity, with a time scale tau equal to 3 pi mu r to the fourth over 4fh0 squared. 

00:04:17,579 --> 00:04:26,920 [Pranav]
Every case collapses onto one single curve. h0 by h whole squared gives us 1 plus t over tau. For the lab defaults, 

00:04:31,120 --> 00:04:48,940 [Pranav]
t is 13.6 seconds, and the time to reach 200, 150 micrometers come out at 17, 100-uh, 109 and 475 seconds respectively. Next, how the simulator generalizes beyond a disc. 

00:04:51,920 --> 00:05:31,400 [Pranav]
Closed-form solutions generally exist only for a disc. Real deposits are actually arbitrary shapes, so the lab solves the same equations on a grid. Because the problem is linear, we write the pressure as a fixed shape times the squeeze spread, p equal to 12 mu, uh, over h cubed, uh, times psi. Then psi obeys a Poisson equation. The Laplacian of psi equals minus 1, with psi 0 at the free waste edge and 0 normal slope at the plate wall, which is what keep the paste from leaving the plate. Define s as the integral of psi over the footprint. 

00:05:32,880 --> 00:05:41,980 [Pranav]
The force balance then gives the squeeze spread directly, u equal to fh cubed over 12 mu s, with no iteration. 

00:05:44,260 --> 00:06:24,740 [Pranav]
This is the same mathematical problem as a steady-state conduction with uniform heat source. So one conjugate gradient solver on a 64 by 64 grid serves both pressure and temperature. Each wet cell is balanced by the divergence theorem, and a sub-cell front distance removes the staircase error. The front advances event by event. A dry cell turns wet when it has filled. The elapsed time is ex-advanced exactly because h to the minus 2 is linear in time, and, the gap is reset every, uh, after every single step so that volume is conserved to machine precision. 

00:06:29,960 --> 00:07:00,980 [Pranav]
The simulator, or the simulation can stop in three ways. The paste covers the full plate, the gap reaches a floor of 20 micrometers ie standing in for the filler size, or the force time ends with the dry regions remaining. The solver is validated against the closed forms. For a disc, psi equals r squared minus r squared, uh, over 4, and s equals pi r to the fourth over 8. I'll now show you the live demonstration.

### Section 3
00:00:01,100 --> 00:00:41,320 [Pranav]
Welcome to the Squeeze Lab. Let me show you what I've built. So here, I will take the, the starting values as, 50 newtons of force, with a 40 by 40 mm plate, 100, Pascal-second viscosity, and a gap thickness of 300, micrometers. Um, here I'm showing a single drop placement, but I can also, drag the location of where I place the dot, and I also have made it so that there's an option to, make our own extrusion. Let's try this. 

00:00:48,100 --> 00:00:57,460 [Pranav]
The lab converts the deposit to a pancake whose starting gap is, the paste volume divided by the footprint area. Now I can press play. 

00:01:05,820 --> 00:01:07,560 [Pranav]
Watch the paste spread outward. 

00:01:12,680 --> 00:01:15,740 [Pranav]
You can see this, gap height readout falling, 

00:01:17,780 --> 00:01:21,880 [Pranav]
and also the pressure as a, as represented by the color, 

00:01:23,060 --> 00:01:31,220 [Pranav]
with the, the bluer color showing a lower pressure as expected, which is at the edges, and a higher pressure towards the center, 

00:01:32,700 --> 00:01:34,260 [Pranav]
which is represented by yellow. 

00:01:39,920 --> 00:01:42,440 [Pranav]
This is similar to the parabola which we have derived. 

00:01:44,720 --> 00:01:59,740 [Pranav]
The gap passes the required distances at whatever we've cal-- as whatever we've calculated, which is around 17 seconds for the 200-micrometer mark and about 475 seconds for the 50-micrometer mark. 

00:02:04,540 --> 00:02:05,540 [Pranav]
Now I'll reset it. 

00:02:10,320 --> 00:02:11,760 [Pranav]
Let's try for the single drop. 

00:02:15,000 --> 00:02:20,560 [Pranav]
I'm gonna do a similarity test, changing the viscosity from 100 to 300, 

00:02:23,220 --> 00:02:24,460 [Pranav]
and, uh, replay. 

00:02:35,380 --> 00:02:47,180 [Pranav]
The curve has a similar expected shape, but only the time axis stretches because mu and F only rescale time. At the end, the lab reports whether the paste touches the plate edges. 

00:02:57,140 --> 00:03:01,060 [Pranav]
And only then unlocks the thermal view once the time has been completed. 

00:03:02,540 --> 00:03:04,440 [Pranav]
Next, let me show you the thermal view. 

00:03:11,740 --> 00:03:50,200 [Pranav]
Here's the thermal view. The squeeze has stopped, and the geometry is frozen, so the problem is steady conduction across the gap. An assumption I've made here is that the, uh, thermal effect of the, die does not really affect any of the geometry of the paste. One dimension is enough here because, across-gap gradient exceeds the along-plate gradient by, the square of 1 over epsilon, which is about-- which is of the order of 10 lakhs. Here is the heat flux map. 

00:03:54,180 --> 00:04:05,220 [Pranav]
Fully covered cells carry the, the heat completely through the paste, and, the thermal resistance of, the layer is R times H over the die area. 

00:04:18,459 --> 00:04:21,100 [Pranav]
Here we can see how it achieves steady state. 

00:04:27,660 --> 00:04:29,920 [Pranav]
Let me show you another deposition. 

00:04:43,320 --> 00:04:50,260 [Pranav]
Here, I'm deliberately putting a, a deposit that leaves a corner of the die uncovered. 

00:04:51,280 --> 00:04:55,400 [Pranav]
This will show a different case where there will be, uh, an air pocket. 

00:05:20,840 --> 00:05:34,680 [Pranav]
As you can see, the force duration has ended to the final gap of this, and the paste has clearly not covered the whole dis-- whole plate, as well as, a big chunk here, which comes right under the die. 

00:05:37,160 --> 00:05:38,600 [Pranav]
Let's you go to the thermal view. 

00:05:45,460 --> 00:06:02,444 [Pranav]
Now, as we can see, the die is not covered completely underneath with the thermal paste. It's also having an air pocket. 

00:06:02,444 --> 00:06:27,624 [Pranav]
Now, in the cells where, uh, uh, the air fills the space, uh, the conductivity is 0.0026, which is about 200 times lesser than the paste itself. The two parts have to act in parallel, and so the conductances add, each weighed by its own area based on the formula, which is, um conductivity equal to KL by A. 

00:06:28,924 --> 00:06:43,024 [Pranav]
wait, no, that's resistance. Each weighed by its own area. yeah. So the map shows the dry corner turning cold, which is right here, and the resistances readout climbs. 

00:06:44,284 --> 00:06:59,264 [Pranav]
for a 50-micrometer gap, approximately, as we can see here, the resistance goes from 0.005 Kelvin per watt at full coverage to 0.028 at 90%, 

00:07:00,364 --> 00:07:12,044 [Pranav]
0.036 at 75%, and 0.05 at 50%. Clearly, a bad spread is not at all a small effect. 

00:07:26,204 --> 00:07:58,004 [Pranav]
One practical note, the lab's default 60 Kelvin drop is a legitimate mathematical case, but it's not a real chip. Because for a 100 watt at 62 micrometers, 100-watt chip at 62-micrometer distance, the pace drops about 3.61, uh, 3.1 Kelvin. So we set the die and the heat sink temperatures to differ by that amount. The pace flare itself settles in, uh, about half a millisecond, which we, which we verified with the Fourier number series. 

00:08:01,864 --> 00:08:05,984 [Pranav]
There are also explanations for each module given. 

00:08:10,323 --> 00:08:18,864 [Pranav]
Explanations which have also the equations used and their derivation and what each notation means. 

00:08:30,364 --> 00:09:01,584 [Pranav]
Let's compare whatever we've seen with theory. The peak pressure on screen was twice the mean, and, the parab- as the parabola climbs. The three gap times match the closed form of 17, 109, and, uh, 475 seconds pretty closely. Changing the viscosity only rescaled the time, as we have seen, which is the similarity collapse. And the thermal view reproduced the parallel conductance formula, as we have seen in the graphs. 

00:09:04,924 --> 00:09:20,744 [Pranav]
So a coverage loss shows up directly as lost watts per Kelvin. Three independent checks, one single demonstration. This completes the Newtonian component, and Avanika will now show how her framework handles non-Newtonian pastes.

### Section 4
00:00:01,180 --> 00:00:14,560 [Avanika]
So moving on to how we have implemented the non-Newtonian methods of power-law and Bingham squeeze flow. So if we talk about real pastes, real pastes are filled suspensions. They either have metallic, um, dispersants or 

00:00:15,700 --> 00:00:40,480 [Avanika]
other kind of, uh, silicones. So the Newtonian closure is only the start. Our second component is, uh, our independent model number two. Mo-mostly keeps the, uh, it will keep the conservation untouched, and we will only swap the constitutive stress law. Now, what is the first implementation is the Ostwald-de Waele power law. That is tau equals to K times shear rate to the power n. The linear distribution is unchanged. 

00:00:41,520 --> 00:00:53,600 [Avanika]
The linear stress distribution is unchanged, and we will be inverting the power law to give the velocity profile with the exponent n, uh, plus 1 over n. And shear-thinning paste will have n below 1, 

00:00:55,180 --> 00:01:13,440 [Avanika]
having blunt course and, uh, steep near-wall gradients, and the shear-thickening pastes are more, uh, the velocity profile would look more of a pointed than a pa-parabola. Integrating across the gap and equating to the continuity flux will give us a pressure gradient G, which is proportional to KW to the nr, 

00:01:15,100 --> 00:01:18,220 [Avanika]
uh, to the n over h to 2n plus 1. 

00:01:19,720 --> 00:01:37,600 [Avanika]
So, uh, we have implemented, uh, our non-Newtonian models in this Python notebook. We can see the three constitutive families, uh, where we've, uh, expressed the power laws, and we've taken two different indices for the shear, uh, thinning and shear thickening. And, um, 

00:01:40,840 --> 00:01:42,860 [Avanika]
we have implemented the... 

00:01:48,020 --> 00:02:06,580 [Avanika]
Uh, so this way, we are-- when we're able to integrate across the gap, we get the force as in, as in terms of Scott's law, F equals to 2 pi K over n plus 3 times 2n plus 1 over n to the power n times W to the nr to the n plus 3 over h to 2n plus 1. 

00:02:09,500 --> 00:02:16,440 [Avanika]
And, uh, we are, we're able to also, uh, get the two-phase constant force trajectory 

00:02:17,580 --> 00:02:21,300 [Avanika]
when we are able to implement the constant volume two-phase analysis. 

00:02:25,740 --> 00:02:36,580 [Avanika]
Moving on to, uh, at constant force with volume conservation, the gap is obeys a separable power-law equation. The late-time thinning exponent is minus 2n over 3n plus 5, 

00:02:41,140 --> 00:03:10,000 [Avanika]
uh, minus 0.154 for n equal to 0.5, minus one-quarter for Newtonian, and minus 0.2924, n equal to 1.3. After the paste reaches the die edge, the exponent steepens to minus n over n plus 1. A useful way to see why shear thin-thinning matters is the effective viscosity is K times the shear rate to n minus 1. During the early compression, uh, the wall shear rate is roughly 

00:03:11,460 --> 00:03:29,380 [Avanika]
rw over h square, and it exceeds 100 per second. So for K equal to 100 and n equal to one-half, the effective viscosity falls to about 10 Pascal-seconds, an order of magnitude which is below the Newtonian value. And as the gap closes, the shear rate drops, and the viscosity is able to recover. 

00:03:31,400 --> 00:03:39,940 [Avanika]
Now, uh, moving on to rung two of our implementation is Bingham yield stress squeeze flow, and we follow the Covey-Stanmore cubic. 

00:03:41,040 --> 00:03:51,200 [Avanika]
Uh, so mostly this applies to heavily loaded silver and alumina thermal, uh, paste form of-- which form a percolated particle network, and we define a finite yield stress. 

00:03:53,420 --> 00:04:24,040 [Avanika]
The stress law is tau equals tau y plus m-- mu time-- mu p times shear rate, but only where the shear exceeds the yield stress. Our universal linear stress law immediately predicts the structure. The stress is zero at the mid-plane and the largest at the walls. So a central plug of half thickness, uh, z0 equals tau y over g stays unyielded and flanked by the two sheared layers. Now again, integrating the piecewise velocity gives the Buckingham-Reiner flux, and setting it equal to 

00:04:25,440 --> 00:04:31,320 [Avanika]
rw over 2 produces a cubic equation for the plug fraction, which is, uh, z0. 

00:04:32,440 --> 00:04:42,340 [Avanika]
z0 cubed minus 3 plus 2 times s time, uh, times z0 plus 2 equals 0, where s is the dimensionless local shear parameter. 

00:04:48,100 --> 00:05:11,220 [Avanika]
The Bingham squeeze flow paradox is, um, something that will be further explained. Uh, now setting those two equal gives critical yield stress. The tau y criticals-- uh, the tau y critical equals 3fh over s-- uh, fhc over 2 pi r die cube. So our-- for our GPU configuration with f equal to 400 Newtons, that is 2.8 kilopascals, 

00:05:12,420 --> 00:05:24,740 [Avanika]
we're able to derive at a, a critical height, uh, bond line thickness, and a critical radius for which we are able to, um, simulate the Bingham flow diagrams. 

00:05:29,360 --> 00:05:38,140 [Avanika]
These two ideas make these models trustworthy. The first is the Bingham paradox of Lipscomb and Dunn. Like, a rigid plug cannot exist, 

00:05:39,320 --> 00:06:05,620 [Avanika]
exit while the pla-plates move because mass conservation forces the plug speed to grow with radius. Like, that implies radial and hoop stretching, and therefore vertical compression. So the strain rate invariant inside the core is small, but not zero. The resolution is a weakly deforming pseudo plug. The leading order velocity, pressure, and force are unchanged to the first order in epsilon.

00:06:06,420 --> 00:06:12,280 [Yaswitha]
And in the static stall limit, the deformation vanishes, so the stall thickness is exact. 

00:06:13,300 --> 00:06:36,920 [Yaswitha]
And the second idea is dimensional analysis. With seven variables and three base dimensions, Buckingham's theorem gives four groups: the aspect ratio epsilon, the squeezed Reynolds number, the Bingham number, and a dimensionless force. Like, we track them along every trajectory. Epsilon stays between 10 to the minus 3 to 10 to the minus 2, 

00:06:38,379 --> 00:06:45,920 [Yaswitha]
10 times below the lubrication limit, and the Reynolds number stays between 10 to the minus 12 and 10 to the minus 5. 

00:06:46,960 --> 00:07:16,320 [Yaswitha]
Uh, here the Bingham number diverges as the paste approaches its stall. And finally, the thermal coupling. With the paste radius and gap known, the die splits into a covered core and an air in parallel, air annulus in parallel, like giving an effective resistance and a die average temperature rise. So the uncovered rim also sees as a local one-dimensional air gap penalty, 

00:07:17,560 --> 00:07:27,440 [Yaswitha]
Q double prime times H over K air, K of the air. This uses Fourier's law and the same one-dimensional argument you saw in the lab. 


### Section 5
00:07:30,540 --> 00:08:17,460 [Yaswitha]
Moving on to the results, the setup shared by all five GPU trajectories. The die area is 814 square millimeters, an equivalent radius of 16.1 millimeters. The clamp force is 400 newtons. The dispensed volume is 50 cubic millimeters. The initial dot height is 1 millimeter, and we hold for 60 seconds. Place-- Paste density is 25 kil- 100 kilograms per cubic meter. The Newtonian viscosity and plastic viscosity are 100 Pascal-seconds. The power law consistency is 100 with indices 0.5 and 0.1.3, and the Bingham yield stresses are 250 and 5,000 Pascals. 

00:08:18,780 --> 00:08:38,860 [Yaswitha]
Conductivities are 5 and 0.026. The Newtonian paste reaches the die edge at about 5 se- 5.2 seconds, the shear thickening paste at about 12 seconds, and after that, each follows its phase ruler. So Avnika will now walk through the results. 

00:08:42,020 --> 00:08:44,480 [Avanika]
Uh, let us look at the results starting with the profiles. 

00:08:54,600 --> 00:09:22,800 [Avanika]
Now, uh, at the same flux, we observe that the Newtonian paste peaks at 1.5 times the mean velocity. The shear thinning index of 0.4 gives 1.286. A blunter core and a shear thickening index of 1.3 gives 1.565, a sharper peak. The Bingham profile with a plug fraction of one-half has a completely flat center zone, while the stress profile is the same straight line for all of them. Now, moving on to the figure 3. 

00:09:27,280 --> 00:10:46,920 [Avanika]
Figure 3 will show us about the bondline trajectories on the GPU die. During phase 1, the curves follow the predicted slopes and steepen at the gap thickness of 61 micrometers. After 60 seconds under 400 newtons, the shear thinning paste reaches about 10.8 micrometers and a temperature drop, drop of 1.85 Kelvin. The Newtonian reference reaches 24.6 micrometers, 4.2 Kelvin, and the shear thickening paste reaches about 33 micrometers and 5.7 Kelvin. The shear thinning therefore cuts the temperature drop by about 56% versus the Newtonian, while the thickening makes it about third worse. All of these cover 100% of the die. The Bingham results are where the physics meets reality. With a yield stress of 250 Pascals below the critical 2.8 kiloPascals, the paste is covering the entire die and heads for the area-limited stall of 5.5 micrometers, though at 60 seconds, it is still about, uh, 27 micrometers thick, always thicker than the Newtonian because the yield stress is only adding to the resistance. Now, if we raise the yield stress to 5 kiloPascals, uh, around which would be twice as much, a heavily loaded paste, everything changes. We can see in the figure that the pressure over the die at 60 seconds, 

00:10:48,900 --> 00:11:35,300 [Avanika]
uh, the pressure at 60 seconds is like the paste stalls at 77.3 micrometers with a wetted radius of 14.35 millimeters, and that is only about 79% of the die, leaving a bare silicon ring, which leaves a air annulus, and that is where our thermal bottleneck comes. So thermally, the parallel network makes the temperature drop jump to about 16.7 Kelvin, and the local one-dimensional air gap estimate at the rim is around, uh, 2,000 Kelvin. Treat the number like as an indicator of severity because this lateral spreading in the die and lid would reduce it. But it tells us that the throttling threshold would be crossed, and, uh, that is where our har- hardware bottleneck comes into play. Now, let's take a quick look at figure 5. 

00:11:38,340 --> 00:11:40,560 [Avanika]
So this is a GPU thermal design map, 

00:11:41,740 --> 00:11:59,280 [Avanika]
so with both the Bingham design as well as the power law design space. So here we make it into a design map. The yield stress against clamp force with a white critical locus, uh, which we express in the line, as well as, um, we've also made a partial coverage stall. The figure 4 

00:12:00,620 --> 00:12:01,660 [Avanika]
will tell us about 

00:12:02,680 --> 00:12:05,080 [Avanika]
the club morph-- the plug morphology. 

00:12:06,360 --> 00:12:11,468 [Avanika]
So this is a Bingham plug map. 

00:12:11,468 --> 00:12:19,108 [Avanika]
So a full gap plug at the axis that thin towards the rim, and the master curves for the plug fraction and, uh, the phi of lambda. 

00:12:21,368 --> 00:12:24,628 [Avanika]
Over to Yashwitha to talk about how to interpret these results. 

00:12:25,728 --> 00:12:46,368 [Yaswitha]
Okay. Uh, let us translate these results into engineering decisions for packaging. First, shear thinning is an advantage. So a paste with n around 0.4 to 0.6 flows fast under, under the initial clamp and requires high viscosity at rest. [clears throat] So it thins quickly without pumping out later. 

00:12:48,668 --> 00:13:13,988 [Yaswitha]
Second, yield stress sets a hard stall limit. Increasing filler loading to raise conductivity raises, raises the tau y, and once tau y exceeds the critical value for the clamp force and dispense volume, the paste stalls before reaching the die edge. So the air then costs far more than any gain in bulk conductivity. So the, 

00:13:15,788 --> 00:13:24,288 [Yaswitha]
uh, the third, the remedies. Like, we cannot simply press harder because die cracking load limits are about 400 to 600 Newton, 

00:13:25,448 --> 00:13:42,908 [Yaswitha]
Newtons. So either formulate with dispersants to keep tau y below about 500 pascals while exploiting the shear thinning or change the dispense pattern from a single central P dot to a multiple dot or cross pattern that sho- that shortens the radial travel. 

00:13:43,968 --> 00:14:20,588 [Yaswitha]
And the Newtonian lab supports the same lesson, like coverage and gap, not just conductivity, set the temperature drop. The thermal resistance of the bond line follows the same ordering, about 0.0062 Kelvin per watt for the shear thinning paste and 0.006 Kelvin per watt for the Newtonian, and about 0.008 for shear thickening and 0.00024 for the stalled Bingham paste, like almost 10 times worse than the shear thinning case.

### Section 6
00:00:00,840 --> 00:00:09,220 [Yaswitha]
Moving to the checks and validation, we built an automated suite of 20 tests implementing the seven-point checklist, and every check passes. 

00:00:10,300 --> 00:00:16,560 [Yaswitha]
Coming to the limiting cases, the power law with N equal to 1 reproduces the stefan's solution, 

00:00:17,900 --> 00:00:32,659 [Yaswitha]
4 times into 10 to the power minus 16. The Bingham model with yield stress tending to 0 reproduces Newtonian to 7 times into 10 to the power minus 6, and the thermal network reproduces the full paste and all air limits. 

00:00:34,040 --> 00:01:11,120 [Yaswitha]
Coming to the stall checks, the long time thickness reaches the predicted values, and the static force at the stall point equals 400 newtons to the machine precision. Conservation, volume is conserved. The pressure integral equals the clamp force, and the radial flux equals r W over 2 at every radius and rheology. The last two, 10 to the 10 to the power minus 14 consecutive checks. Stress stays below yield inside the plug. The plug velocity is flat, and the cubic root is exact. 

00:01:13,300 --> 00:01:18,980 [Yaswitha]
Coming to the remaining checks,  the remaining checks target scaling and units. 

00:01:20,120 --> 00:01:27,720 [Yaswitha]
The checks 11 to the 13 fit the late-time slope of each trajectory against the predicted exponent, 

00:01:29,840 --> 00:01:41,300 [Yaswitha]
minus 2 and over 3N plus 5 for N equal to 1.5 and 1.3 with errors below 3 times 10 to the minus 10. 

00:01:42,580 --> 00:01:52,160 [Yaswitha]
Check 14 rescales the base units of mass, length, and time arbitrarily and confirms the gap history is invariant, which is dimensional homogeneity. 

00:01:53,600 --> 00:02:05,740 [Yaswitha]
And we also cross-check the two components against each other. The Newtonian lab and the power law model share the stiffened limit, so the gap laws agree at N equal to 1. 

00:02:08,699 --> 00:02:31,800 [Yaswitha]
And while preparing this video, we rederived every headline number. We found one real mistake in our earlier draft. The critical yield stress had been quoted as 1.38 kilopascals, but the correct value from our own stall equations is 2.8 kilopascals, a missing factor of pi. We also reran the 60-second 

00:02:32,860 --> 00:02:49,420 [Yaswitha]
table for the shear thickening and low-yield Bingham pastes, and the values you heard are the corrected ones. That is the point of verification. It catches us before the physics does. Like, each test has an explicit tolerance, and none was loosened to make it pass. 

00:02:52,200 --> 00:03:04,760 [Yaswitha]
Finally, we audited our physical assumptions against reality across all five trajectories, shown here in Figure 6 on the page 18. On the left panel, the geometric aspect ratio epsilon, 

00:03:05,840 --> 00:03:10,200 [Yaswitha]
that is H over R, stays between 10 power minus 3 and 10 power minus 2. 

00:03:11,320 --> 00:03:20,780 [Yaswitha]
Well, below the 0.1 lubrication breakdown line, right below it, the squeezed Reynolds number stays between 10 power minus 12 and 10 power minus 5, 

00:03:22,080 --> 00:03:37,380 [Yaswitha]
confirming creeping flow with negligible inertia. On the right panel, the Bingham number cleanly tracks the crossover from viscous-dominated squeeze to plastic stall divergence as H approaches the H star. 

00:03:38,960 --> 00:04:01,060 [Yaswitha]
And we also checked neglected effects in the Newtonian lab. Gravity contributes only about 2 and a half pascals against 10, tens of kilopascals applied. And compressibility at a 2 kilo- gigapascal bulk modulus shifts the final gap by just 1.6 into 10 power minus 15. 

00:04:06,400 --> 00:04:10,200 [Yaswitha]
Now, Avanika will now close with the limitations and conclusions.

### Section 7
00:00:00,480 --> 00:00:23,040 [Avanika]
Um, so for the final part, let's start with a wrap-up. And, uh, so w- the final implementations and the further extension of this, uh, the further scope of this project can be working with AI and being able to simulate these work, uh, simulate these fluid flows in real time. So we have asked AI to done-- do that, and this, these, there are two AI-rendered flows, which is, which you can see on the, 

00:00:24,460 --> 00:00:36,540 [Avanika]
um, repository. So we have AI-rendered simulations, both of which are runnable, but, uh, we haven't been, uh... So for further scope of this project can be working with AI and being able to verify them, um, 

00:00:37,820 --> 00:01:01,960 [Avanika]
and so that we can actually visualize these fluid flows in real time. Now, moving on to what our project's, uh, final, um, like what are the assumptions we're making and what are the parts that we're leaving out? So one thing we've modeled is a Newtonian flow, which gives us a clean baseline, but it's never being able to address the flow. It is something that it, it just keeps running and, uh, as like indefinitely with time, 

00:01:03,200 --> 00:01:28,400 [Avanika]
uh, which is also, um, yeah, the pace keeps staying indefinitely with time. The second, uh, fluid flow that we discovered was the shear thinning under the power law, uh, where it captures the viscosity dropping under high stress, uh, high shear rates, yet it has no yield stress, bec- meaning it starts flowing even under a tiny supplied force. Then when we talk about the Bingham flow diagram, uh, the... 

00:01:29,760 --> 00:03:31,300 [Avanika]
what do we understand from that is like we're able to introduce a yield stress, we're able to put in a rest condition, but there is again a fallback where there is, uh, no shear thinning above the yield, and once yield is ex- exceeded, the stress scales linearly with the shear rate. So with these, uh, three models, if you want to, uh, model real, real-time, uh, real-life, uh, TIMs, we realize that we need to kind of co- come to a, a trade-off point between these two models. So we, in reality, these TIMs exhibit both the yield behavior as well as the shear thinning behavior, and, uh, we try to bring in this Herschel-Bulkley model, which basically, uh, introduces tau equal to tau y plus K, uh, shear rate to the power n. Now, the good news about our mod- di-modular approach or bimodal approach is that, uh, with the, because of the modularity, we're able to directly implement this Herschel-Bulkley model, uh, where it's able to get into, it's able to being implemented in our existing framework. And all we have to do is just change the stress law, the constitutive law, uh, without requiring to change anything about the conservation equations. And, um, what are the, uh, what, what can we, what... So when we talk about the, uh, how much we're able to model and how much we're not able to model, we weren't able to model the, we weren't able to account for certain real-life aspects such as, uh, filler jamming at the minimum bond line thickness because the solid particles halt thinning regardless of the pressure, and temperature-dependent viscosity wasn't being able to... We weren't, we didn't implement a temperature-dependent viscosity because it will change, uh, both the assembly and the operation. And, uh, geometric, uh, asymmetries weren't accounted for because, uh, we could have a die or a heat sink tilt and off-center paste dispensing, and we didn't account for thermal, uh, contact resistance at the interface, um, where we can... as well as like the air voids and the pump-out, which is driven by repeated thermal cycling. And we also didn't account for lateral heat spreading. So one, 

00:03:32,740 --> 00:03:39,420 [Avanika]
uh, so we just applied a one-dimensional hotspot treatment, which was neglecting, uh, lateral heat spread. 

00:03:40,440 --> 00:04:25,840 [Avanika]
Uh, what is, uh, for, like, what can we do to model real-life TIMs is, uh, uh, like we need to, like, we need to have a experimental rheology, and we need to get parameters from these measurements rather than just solely, uh, uh, relying on, uh, assumed parameters. So what are the things that we could extract is the consistency index K, the flow behavior n, and the yield stress tau. So all of these quantities can be, uh, ex- can be extracted. And having measured parameters grounds the model in real material behavior and show how closely the different commercial or lab formulation match these idealized closures. And, uh, we can develop a model which can, uh, exactly model real-life TIMs. 

00:04:26,980 --> 00:04:27,980 [Avanika]
Um, moving on to, 

00:04:29,480 --> 00:05:06,540 [Avanika]
uh, we can progressively, like, layer the real-world physics by coupling viscosity to temperature, so local heating fee- local heating feeds back into the flow resistance and the thinning dynamics. We can account for the minimum bond line limits, the filler jamming, and the non-ideal geometry that we just discussed about. And, uh, yeah, we can extend it to the thermal side beyond the 1D hotspot. We can incorporate lateral spreading. We can also talk about long-term degradation mechanisms, which usually, uh, happen in real-life hardware chips, where there is voiding or there's some pump-out under thermal cycling. So in real-life chips, uh, one major, uh, 

00:05:07,680 --> 00:05:23,940 [Avanika]
bottleneck is basically that it's not just a temperature being uniformly applied, but rather the die is undergoing heating, a constant loop of, uh, heating and cooling cycles. So it has to account for that. There will be degradation mechanisms, and we can extend this model to account for those too. 

00:05:25,400 --> 00:06:34,204 [Avanika]
And finally, uh, what can we do for this model is we can, we can have direct experimental validation, where we can compare the model-predicted bond line thickness and the thermal rises against physical measurements on text fixtures and hardware. Uh, right now, we state openly that our results are validated for internal consistency and the limiting cases. It is not yet against a physical, uh, TIM sample. And closing that gap is a milestone that turns this framework from a verified mathematical model into a validated design tool, and that increases the scope and the application of this project. Uh, now, what were we able to achieve and what were the three questions that we kept asking ourselves is, how thick is the layer? How long does it take for this to, um... Thin out to a specific bond line thickness. So we realized that the Newtonian paste thins as T power minus 1 by 4 and T power minus 1 by 2 without ever coming to a complete stop. The shear thinning is able to accelerate the thinning process. And in contrast to this, the yield stress arrests the flow at finite bond line, um, uh, thickness, which we derived as a critical bond line thickness using the Bingham model. And, 

00:06:35,784 --> 00:07:15,884 [Avanika]
um, we also have to... Another question was like, how many, uh, temp- how much was the temperature drop? Were we able to get some significant figures is yes. So with our benchmark of 700-watt GPU reference case, the difference is dramatic. Were we able to saw around, uh, 1.85 Kelvin for a well-behaved shear-thin paste, and for a Bingham paste, that was about 16.7 Kelvin, which is a huge difference. And that is why we were able to, uh, visually see how these models could affect something as important as a temperature rise, which is the where the entire thermal bottleneck is being addressed, and thermal throttling, as introduced in the, as introduced in the beginning. 

00:07:17,164 --> 00:07:40,884 [Avanika]
Um, and how far, like, what are our assumptions? Are our assumptions even useful when it comes to, um, application is yes. We did take, uh, uh, more assumptions because we wanted to model something simple, but somewhere along the way, the mathematics did get a lot complicated. Uh, but however, verifications all passed. We have 20 verification tests which is being run in the repository, 

00:07:42,424 --> 00:07:45,724 [Avanika]
uh, under the non-Newtonian model I worked on. So we can, 

00:07:46,984 --> 00:07:52,784 [Avanika]
uh... So all this has a workflow which verifies all these physics, and we're able to, um, 

00:07:54,184 --> 00:08:56,004 [Avanika]
get standard results out of them. So there we go when it comes to the verification. So our model is solid when it comes to, uh, whether the assumptions hold and what are the margins for them, all defined in the report. Uh, finally, we have to talk about what, how did transport phenomena shape this project, uh, uh, entirely. It's because conservation laws are universal, and these closures are material-specific. We were able to model different closures for one particular fluid, which is the thermal paste, and, uh, combining the single continuity flux, a linear stress balance, and we had three different flow closures. Like, the overall, the overlying thermal network gives us an end-to-end chain, like which starts from the clamp force to the junction temperature. And one important design rule that we learned is that whatever it is, the paste yield stress should be below the critical threshold, and that way we can favor the thinning, uh, the shear thinning behavior, and we can, uh, effectively thin the material under the load without stalling it prematurely. 

00:08:57,124 --> 00:09:44,504 [Avanika]
So we work with all these laws to just model that critical, uh, yield stress, and that is all the model is. So this has been a very, uh, informative as well as, uh, a thorough learning process where we learned how we can shift these abstract physical equations from the transport phenomena course into addressing a real-life, uh, problem, which is the thermal bottlenecks in the chips. And we also realized there's so much scope to this. Just by modeling these, uh, diagrams and simulating them, we realized how far we can actually not just simulate these problems, but also be able to solve them one day through these simulations themselves. And all of this just from knowing these underlying physics equations and these laws which shape these, um, fluid flows. So yeah, thank you for the opportunity, 

00:09:45,584 --> 00:09:51,104 [Avanika]
and, uh, we can... The, the results are reproducible through the repository. Thank you.



