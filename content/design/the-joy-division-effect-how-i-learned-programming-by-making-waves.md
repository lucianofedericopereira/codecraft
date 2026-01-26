---
title: "The Joy Division Effect: How I Learned Programming by Making Waves"
date: 2026-01-26
comments: true
toc: true
---

Exploring how a static pulsar plot from 1970 became the spark that led me to understand Perlin noise, animation, and the beauty of coherent randomness. Turning Unknown Pleasures into moving waves taught me more about programming than any textbook ever did.

## 4K Before 4K

Back then, “4K” didn’t mean ultra‑HD — it meant 4 kilobytes. Tiny intros that somehow squeezed whole worlds of motion, color, and attitude into the space of a modern emoji pack. And somewhere in that neon‑washed universe of pixels pretending to be ultra‑HD, with synth lines stretching into cosmic gradients, one image kept resurfacing in my mind: the waveform from Joy Division’s *Unknown Pleasures*.

That stark, minimalist cover showed something I couldn’t unsee — a still image that wanted to move. Those parallel mountain ranges weren’t Perlin noise at all, but stacked plots of radio pulses from the pulsar CP1919. Still, to my kid‑programmer brain, they looked like frozen waves begging to be animated, pulsing, breathing.

## From Stillness to Motion

On my Commodore 64, armed with assembly language and pre‑calculated prime numbers (because true randomness was too expensive), I tried to animate what I saw. Sine waves came first: too perfect, too predictable. Then I tried more complex LFOs, but they still lacked that organic wobble I was chasing.

Just to be clear, the original CP1919 pulsar plot — the one used on *Unknown Pleasures* — does not move. It’s a stack of 80 separate recordings, each one a single rotation of the pulsar. Think of it like 80 screenshots of a repeating signal.

But what I wanted wasn’t the science — it was the *feeling* of those lines coming alive. And to get that, I needed something the real data couldn’t give me.

## Perlin Noise: So 80s.

Years later, I realized I’d been trying to reinvent Perlin noise without knowing it existed. Ken Perlin’s 1983 algorithm for generating natural‑looking textures was exactly what I’d been reaching for: coherent randomness, smooth transitions — the mathematical equivalent of something alive.

Perlin created his noise function while working on *Tron*, trying to avoid the rigid, grid‑like look that early CGI couldn’t escape. He later described the method in a paper called **“An Image Synthesizer,”** which remains one of the most accurate names ever given to a graphics technique. Between *Tron*, synth aesthetics, vector graphics, and that title, the only thing missing is *The Breakfast Club* and you’ve basically assembled the entire 80s in one algorithm.

The core idea behind Perlin noise is simple: generate variation that isn’t repetitive like a sine wave and isn’t chaotic like pure randomness. It produces values that drift smoothly — exactly the behavior I could never coax out of lookup tables, LFOs, or prime‑indexed hacks.

## How 1D Perlin Noise Works

The one‑dimensional version goes like this:

- take the two integer positions around your input  
- assign each a pseudo‑random gradient  
- compute each gradient’s influence  
- blend the results using a smooth interpolation curve  

That interpolation step is what removes the mechanical edges and creates the “organic” motion the *Unknown Pleasures* cover hints at.

Once you understand that, animating the lines becomes straightforward. Each horizontal line samples a slightly different position in the noise field. Each x‑coordinate marches forward through noise space. A height table shapes the silhouette so the lines rise and fall like the original pulsar plot. Everything else is just drawing.

## Let’s Bring in JavaScript

The JavaScript version below keeps only the essentials: a permutation table for repeatable pseudo‑random values, a precomputed fade curve for smooth transitions, and a compact 1D noise function. A height table controls how much each point can move, creating the familiar rise in the center and fall at the edges. Each line reads from a slightly different position in the noise field, and each x‑coordinate steps forward to preserve the tiny spikes and irregularities that make the motion feel alive.

### Relevant Parts of the Code

- **Permutation table** (`perm`):  
  A 512‑entry table used to generate repeatable pseudo‑random gradients — the backbone of classic Perlin noise.

- **Fade table** (`fadeTable`):  
  A precomputed smoothing curve. Instead of calculating the fade function every frame, the code looks it up, which is faster and avoids unnecessary floating‑point work.

- **Height table** (`hTable`):  
  Defines how tall each line can be at each x‑coordinate. This creates the “mountain” profile: low at the edges, high in the center.

- **Noise function** (`noise(x)`):  
  A compact 1D Perlin implementation that finds the integer cell around `x`, computes the fractional part, and blends the two gradient contributions using the fade curve. The result is a smooth value between 0 and 1.

- **Animation loop** (`animate()`):  
  Draws stacked horizontal lines. Each line samples the noise field with a different offset (`this.t + idx * this.step`), uses the height table to scale the displacement, and fills and strokes the shape to create the solid *Unknown Pleasures* look.

The key detail is the `idx++` inside the inner loop. That increment ensures each x‑coordinate samples a unique position in the noise field, preserving the tiny spikes and irregularities that make the waveform feel alive.

## What the Code Is Doing, Conceptually

In practical terms:

- initialize noise tables  
- build the permutation table, fade curve, and height profile  
- for each animation frame:  
  - clear the canvas  
  - loop over horizontal lines  
  - for each x‑coordinate:  
    - compute a Perlin noise value  
    - multiply it by the height table  
    - subtract it from the baseline y‑position  
    - draw the resulting shape  
- advance time (`this.t += 0.01`) to shift the sampling position  
- request the next frame  

That’s all the algorithm needs: a smooth noise source, a height profile, and a stack of lines sampling the noise field at different offsets.

## The Result

[example:3]
