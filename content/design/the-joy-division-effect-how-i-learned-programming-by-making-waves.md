---
title: "The Joy Division Effect: How I Learned Programming by Making Waves"
date: 2026-01-26
comments: true
toc: true
---

## 4K Before 4K

Back then, “4K” didn’t mean ultra‑HD — it meant 4 kilobytes. Tiny intros that somehow squeezed whole worlds of motion, color, and attitude into the space of a modern emoji pack. And somewhere in that neon‑washed universe of pixels pretending to be ultra‑HD, with synth lines stretching into cosmic gradients, one image kept resurfacing in my mind: the waveform from Joy Division’s Unknown Pleasures.

That stark, minimalist cover showed something I couldn’t unsee — a still image that wanted to move. Those parallel mountain ranges of radio‑telescope data looked like frozen waves, and my kid‑programmer brain insisted they should be alive, pulsing, breathing.

## From Stillness to Motion

On my Commodore 64, armed with assembly language and pre‑calculated prime numbers (because true randomness was too expensive), I tried to animate what I saw. Sine waves came first: too perfect, too predictable. Then I tried more complex LFOs, but they still lacked that organic wobble I was chasing.

## Perlin noise: So 80s.

Years later, I realized I’d been trying to reinvent Perlin noise without knowing it existed. Ken Perlin’s 1983 algorithm for generating natural‑looking textures was exactly what I’d been reaching for: coherent randomness, smooth transitions — the mathematical equivalent of something alive.

Perlin created his noise function while working on Tron, trying to avoid the rigid, grid‑like look that early CGI couldn’t escape. He later described the method in a paper called An Image Synthesizer, which remains one of the most accurate names ever given to a graphics technique. Between Tron, synth aesthetics, vector graphics, and that title, the only thing missing is The Breakfast Club and you’ve basically assembled the entire 80s in one algorithm.

The core idea behind Perlin noise is simple: generate variation that isn’t repetitive like a sine wave and isn’t chaotic like pure randomness. It produces values that drift smoothly — exactly the behavior I could never coax out of lookup tables, LFOs, or prime‑indexed hacks.
How 1D Perlin Noise Works

## The one‑dimensional version goes like this:

- take the two integer positions around your input
- assign each a pseudo‑random gradient
- compute each gradient’s influence
- blend the results using a smooth interpolation curve

That interpolation step is what removes the mechanical edges and creates the “organic” motion the Unknown Pleasures cover hints at.

Once you understand that, animating the lines becomes straightforward. Each horizontal line samples a slightly different position in the noise field. Each x‑coordinate marches forward through noise space. A height table shapes the silhouette so the lines rise and fall like the original plot. Everything else is just drawing.

## Let’s Bring in JavaScript

The JavaScript version below keeps only the essentials: a permutation table for repeatable pseudo‑random values, a precomputed fade curve for smooth transitions, and a compact 1D noise function. A height table controls how much each point can move, creating the familiar rise in the center and fall at the edges. Each line reads from a slightly different position in the noise field, and each x‑coordinate steps forward to preserve the tiny spikes and irregularities that make the motion feel alive.
Relevant Parts of the Code

- **Permutation table** (perm): _A 512‑entry table used to generate repeatable pseudo‑random gradients — the backbone of classic Perlin noise._
- **Fade table** (fadeTable): _A precomputed smoothing curve. Instead of calculating the fade function every frame, the code looks it up, which is faster and avoids unnecessary floating‑point work._
- **Height table** (hTable): _ Defines how tall each line can be at each x‑coordinate. This creates the “mountain” profile: low at the edges, high in the center._
- **Noise function** (noise(x)): _A compact 1D Perlin implementation that: finds the integer cell around x, computes the fractional part, blends the two gradient contributions using the fade curve. The result is a smooth value between 0 and 1._
- **Animation loop** (animate()) : _Draws stacked horizontal lines. Each line: samples the noise field with a different offset (this.t + idx * this.step), uses the height table to scale the displacement, and fills and strokes the shape to create the solid Unknown Pleasures look.

The key detail is the idx++ inside the inner loop. That increment ensures each x‑coordinate samples a unique position in the noise field, preserving the tiny spikes and irregularities that make the waveform feel alive.

### What the Code Is Doing, Conceptually

In practical terms:

- Initialize noise tables
- Build the permutation table, fade curve, and height profile.
- For each animation frame: 1) clear the canvas 2) loop over horizontal lines 3) 
- for each x‑coordinate, compute a Perlin noise value: 1) multiply it by the height table 2) subtract it from the baseline y‑position 3) draw the resulting shape
- Advance time (this.t += 0.01)  
- This shifts the sampling position in the noise field, creating motion.
- Request the next frame  
- And the animation continues.

That’s all the algorithm needs: a smooth noise source, a height profile, and a stack of lines sampling the noise field at different offsets.

## The Result

[example:3]
