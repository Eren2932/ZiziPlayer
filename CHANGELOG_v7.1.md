Zizi Player 7.1.0 (versionCode 9)
Hotfix on top of 7.0.0. One critical bug, one wrong colour model, one wrong icon set.
1. CRITICAL: the app stopped responding to every tap
Symptom: after a while nothing reacts - transport buttons, tabs, search, favourites. The UI still
draws, lists still scroll under the finger, playback keeps going. Killing and reopening the app from
recents does not help.
Cause: the sheet scaffold introduced in 7.0.0. Dismissal was performed on the line after the
exit animation:
closing = true
scope.launch { offset.animateTo(height, tween(150)); onDismiss() }   // 7.0.0
An Animatable cancels its running animation the moment anything else touches it. Any second gesture
inside those 150 ms - a flick, a finger landing on the sheet, a double tap on the scrim - made
draggable's snapTo cancel the exit animation, the CancellationException killed the coroutine,
and onDismiss() was never reached. closing stayed true forever, so every later tap hit
if (closing) return.
What stayed on screen was a full screen, focusable Popup whose scrim alpha is 1 - offset / height
i.e. 0 once the sheet has slid down. An invisible window, above everything, in its own window, swallowing every touch event in the app. It survives leaving and re-entering the app because the composition is still alive. Reproduction: open the queue, flick it down and immediately flick again.
Fix, structural:
Dismissal is owned by state, not by an animation. closing = true is the request; a separate effect runs the exit and dismisses afterwards outside the animation's cancellation path.
That effect is wrapped in withTimeout(exit + 120 ms), so a wedged animation cannot hold the sheet.
While closing, the scrim's gesture detector and the drag handle are disabled - nothing can interrupt an exit already under way.
The scrim's pointerInput exists only while the scrim is visible: an invisible layer can never be the thing eating touches again.
Popup(focusable = ...) is false while closing, so the window releases input focus immediately.
Also: the sheet no longer restarts its entry animation when its content grows (a switch flipping, the
cache size arriving), and the queue sheet opts out of the scrolling container - a LazyColumn inside a
verticalScroll was fighting the parent for every drag.
2. The backdrop now really is the cover's colour
7.0.0 built the gradient in HSV: fixed "value" per stop, saturation capped at 0.32. HSV is not
perceptual - "value 0.24" is a clean navy for a blue hue and olive mud for a yellow one. That is the
"tries to sit on the cover and looks awful in some zone" case, verbatim.
Measured off the reference player, left edge, one pixel column, converted to Oklch:
y	0.03	0.07	0.12	0.30	0.40	0.52	0.62	0.70	0.80	0.90
L	.124	.161	.199	.254	.278	.305	.334	.342	.294	.234
C	.011	.012	.017	.025	.027	.030	.035	.034	.029	.018
h	134	151	145	149	145	141	140	140	139	142
Three facts, all three of which 7.0.0 got wrong:
The hue is constant - five degrees of drift over the whole screen, and it is the cover's hue (149). 7.0.0 built seven stops from five different swatches: on the sunflower cover the backdrop hue crawled 65 -> 83 -> 108 -> 136 -> 161 top to bottom. Brown at the title, green at the controls.
Chroma tracks lightness, C = 0.104 x L. Dark bands are nearly grey, the bright band under the controls carries the colour. A flat saturation cap cannot express that.
The peak sits at 67 % of the height at L = 0.334 - brighter than 7.0.0 aimed for.
7.1.0 works in Oklch: one hue for the whole screen (chroma-squared weighted circular mean of the
swatches, so a grey shade cannot drag a colourful cover), the measured L ramp, C = k x L with
k = 0.085 + peakChroma x 0.42 clamped to [0.085, 0.140] - which reproduces the reference's 0.104
exactly for the reference cover. Out-of-gamut colours give up chroma, never hue, so the tint does not
shift as bands get darker. Each theme scales the ramp by its own base lightness, so AMOLED stays
AMOLED. The second radial glow 7.0.0 added under the controls is gone: that band is part of the ramp
now, and stacking two washes on top of it is what produced glare on warm covers.
3. Transport icons are drawn, not imported
Measured bounding boxes in the reference against what 7.0.0 shipped:
glyph	reference	7.0.0
shuffle	18.8 x 14.4 dp, round caps	Material 24 x 24, square caps
skip prev / next	16.9 x 18.8 dp	Material 34 x 34
pause	two bars 12.5 dp wide, 33.8 dp tall, 6.25 dp gap	Material glyph in a 52 dp box
repeat / repeat one	18.8 x 18.8 dp, round caps	Material 24 x 24
All five are now paths built once per size inside drawWithCache: no ImageVector parsing, no vector
tree, no per-frame allocation, round caps and joins that match. Touch targets stay 44-72 dp - the
drawn size and the tappable size are deliberately separate.
The row is positioned, not arranged. Measured centres as a fraction of screen width: 0.097, 0.316,
0.500, 0.682, 0.903 - deliberately uneven, which Arrangement.SpaceBetween can never produce. A
three line custom Layout places each child on its centre in one measure pass. The mini player uses
the same glyphs.
Press feedback: a scale spring inside graphicsLayer (0.86, damping 0.55, stiffness 2600), so
pressing a button repaints one layer instead of recomposing the transport row.
