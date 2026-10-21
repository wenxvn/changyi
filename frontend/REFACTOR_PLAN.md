# Frontend Optimization & Algorithm Showcase Plan

## Overview
Transform the medical triage UI from text-heavy, rigid layout to a dynamic, visual-first experience that showcases the core algorithm through immersive interactions.

## Core Objectives
1. **Reduce AI taste** - Less descriptive text, more visual hierarchy
2. **Showcase algorithm** - Make Safety Gate, confidence, and routing visible
3. **Enhance 3D integration** - Agent becomes interactive, not decorative
4. **Dynamic layouts** - Fluid, responsive components that adapt to content importance

---

## Phase 1: Core Algorithm Visualization Components

### 1.1 Safety Gate Status Orb
**New Component**: `SafetyGateOrb.tsx`
- Large 3D status sphere that changes based on triage status
- States:
  - `EMERGENCY`: Red pulsing sphere with urgent animation
  - `URGENT`: Orange glowing sphere with warning pulse
  - `ROUTINE`: Green calm sphere with gentle breathing
  - `INSUFFICIENT_INFORMATION`: Gray incomplete sphere showing gaps
- Props: `status`, `animated`, `size`
- CSS: Glassmorphism, gradient overlays, particle effects

### 1.2 Confidence Visualization
**New Component**: `ConfidenceRing.tsx`
- Circular progress indicator showing information completeness
- Animates from current % to new % when followup answered
- Shows: `[Filled segment]` Known + `[Empty segment]` Missing
- Props: `confidence`, `previousConfidence`, `animated`
- Integration: Replaces text "信息不足" with visual gauge

### 1.3 Department Route Strength
**New Component**: `DepartmentRouteBar.tsx`
- Horizontal strength bars for department candidates
- Shows relative matching scores (not medical confidence)
- Props: `departments[]`, `highlight`, `showComparison`
- Animation: Bars grow in sequence on mount
- Integration: Replaces plain list in `htriage_analysis`

### 1.4 Algorithm Stage Flow
**Enhanced Component**: `ProgressiveStatus.tsx`
- Transform from linear list to flowing visual timeline
- Each stage gets icon, current state, and micro-animation
- Safety Gate stage is visually emphasized (larger, different style)
- Props: Add `emphasizeStage?: string` to highlight key algorithms

---

## Phase 2: HomePage Redesign

### 2.1 Hero Section Simplification
**Changes to `HomePage.tsx`:**
- Remove verbose explanatory text
- Single large input + one CTA
- CareAgent moves to center, becomes larger
- Example symptoms: Smaller, bottom placement
- Hero promise badges: Convert to subtle icons only

**Layout:**
```
┌─────────────────────────────────────┐
│      [Large CareAgent 3D]           │
│                                     │
│   [Symptom Input - Centered]       │
│   [Submit Button]                  │
│                                     │
│   [Example chips - subtle]         │
└─────────────────────────────────────┘
```

### 2.2 Process Section Enhancement
- CarePath visualization stays
- Add animated flow when hovering over steps
- Remove explanatory paragraph, replace with interactive discovery

### 2.3 Philosophy Section
- Keep principles but make visual:
  - Each principle gets large icon
  - Title stays, but description shortens to 1 sentence
  - Cards become hoverable with depth effect

---

## Phase 3: TriagePage Transformation

### 3.1 Result Display Revolution
**Major changes to `TriageResults.tsx`:**

**Before:**
- Status pill + text headline
- Long explanation paragraph
- Linear care steps
- Flat department display

**After:**
- `SafetyGateOrb` dominates top (large, animated)
- Status in 1 line below orb
- Department shown with `DepartmentRouteBar`
- Care steps: Convert to vertical flowing timeline with icons
- All explanatory text moved to expandable "Why?" section

**New Layout:**
```
┌─────────────────────────────────────┐
│                                     │
│      [SafetyGateOrb - Large]       │
│      🟢 常规就医                    │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━      │
│                                     │
│  主要方向                           │
│  呼吸内科  ████████░░ 85%          │
│                                     │
│  [点击展开依据 ↓]                  │
└─────────────────────────────────────┘
```

### 3.2 Interactive Algorithm Evidence
**New Component**: `AlgorithmEvidence.tsx`
- Collapsible section for "Why this recommendation?"
- Shows:
  - Matched symptom tags (highlighted in user's text)
  - Department scoring breakdown
  - Red flags (if any)
  - Followup impact (before/after comparison)
- Default: Collapsed
- User clicks to expand and explore

### 3.3 Followup Questions Redesign
**Enhanced**: `FollowupPrompt.tsx`
- Remove verbose intro text
- Show confidence ring: "60% complete"
- Questions as interactive cards (not form fields)
- Each answer updates confidence ring with animation

### 3.4 Agent Integration
**Enhanced**: `CareAgent` component
- Agent size adapts to stage:
  - `idle`: Medium
  - `submitting`: Large (takes focus)
  - `waiting`: Large with active animation
  - `result_ready`: Small, moves to side
  - `emergency`: Large, red coloring
- Remove bottom disclaimer text, show only on demand

---

## Phase 4: 3D Enhancements

### 4.1 AgentScene Improvements
**Changes to `AgentScene.tsx`:**
- Add stage-specific visual states:
  - `emergency`: Core turns red, particles scatter
  - `needs_followup`: Core pulses with question indicator
  - `composing`: Particles move toward center (listening)
  - `result_ready`: Gentle glow, settled state
- Increase particle count for richer visuals
- Add subtle post-processing glow effect

### 4.2 New 3D Component: SafetyGateOrb
**New file**: `SafetyGateOrb.tsx`
- Three.js sphere with dynamic materials
- Status-driven color and animation
- Can be used standalone or integrated into scenes
- Optimized for mobile (fallback to CSS animation)

### 4.3 Particle Flow Effect
**New utility**: `ParticleFlow.tsx`
- Small floating particles that react to scroll
- Used in hero section background
- Subtle, non-distracting

---

## Phase 5: CSS Architecture Cleanup

### 5.1 Reduce Visual Clutter
**Changes to `globals.css`:**
- Remove borders from most cards
- Use shadow + subtle background instead
- Increase whitespace between sections
- Simplify eyebrow/label styles (fewer, larger)

### 5.2 Typography Hierarchy
- H1: Larger, more impactful
- Body: Reduce density by 20%
- Labels: Fewer colors, consistent sizing
- Remove redundant "eyebrow" + "heading" patterns

### 5.3 Animation Library
**New**: `animations.css`
- Centralize all micro-interactions
- Consistent easing and timing
- Reusable animation classes

### 5.4 Component-Specific Styles
- `.safety-gate-orb`: New styles for orb component
- `.confidence-ring`: Ring visualization styles
- `.department-route`: Horizontal bar styles
- `.algorithm-evidence`: Collapsible evidence panel

---

## Phase 6: Mobile Optimization

### 6.1 Responsive Breakpoints
- Orb size scales down on mobile
- Department bars stack vertically
- CareAgent becomes smaller, less prominent
- Text hierarchy adjusts (smaller but still readable)

### 6.2 Touch Interactions
- Larger hit targets for all interactive elements
- Swipeable card galleries for hospitals/doctors
- Pull-to-refresh consideration

---

## Implementation Order

### Week 1: Core Components
1. ✅ SafetyGateOrb component (3D + fallback)
2. ✅ ConfidenceRing component
3. ✅ DepartmentRouteBar component
4. ✅ AlgorithmEvidence component

### Week 2: Page Redesigns
1. ✅ HomePage hero simplification
2. ✅ TriagePage result section transformation
3. ✅ Followup UI enhancement
4. ✅ Agent stage-driven sizing

### Week 3: 3D & Animation
1. ✅ AgentScene stage-specific visuals
2. ✅ SafetyGateOrb integration
3. ✅ Particle flow background
4. ✅ Micro-animations polish

### Week 4: Polish & Testing
1. ✅ CSS cleanup and optimization
2. ✅ Mobile responsive testing
3. ✅ Performance optimization
4. ✅ Cross-browser testing

---

## Success Metrics

### Visual Hierarchy
- [ ] User can identify safety status in <1 second
- [ ] Department recommendation visible without scrolling
- [ ] No more than 3 text blocks above the fold

### Algorithm Showcase
- [ ] Safety Gate is visually prominent
- [ ] Confidence level is always visible
- [ ] Department scoring is interactive
- [ ] Algorithm stages are clear but not overwhelming

### 3D Integration
- [ ] Agent animation matches user action
- [ ] Status orb changes are noticeable
- [ ] 3D elements enhance, not distract

### Text Reduction
- [ ] 40% less text on first screen
- [ ] Key information stays, explanations collapse
- [ ] Labels are concise (max 3 words)

---

## Technical Considerations

### Performance
- Lazy load 3D components
- Use CSS animations for simple states
- Throttle scroll-based effects
- Maintain 60fps on mid-range devices

### Accessibility
- All visual states have text equivalents
- Color not sole indicator of meaning
- Keyboard navigation preserved
- Screen reader friendly labels

### Browser Support
- WebGL2 for modern browsers
- SVG fallback for older/constrained devices
- CSS feature detection for animations
- Graceful degradation throughout

---

## File Structure

```
src/
├── components/
│   ├── algorithm/              # New
│   │   ├── SafetyGateOrb.tsx
│   │   ├── ConfidenceRing.tsx
│   │   ├── DepartmentRouteBar.tsx
│   │   └── AlgorithmEvidence.tsx
│   ├── agent/
│   │   ├── AgentScene.tsx      # Enhanced
│   │   ├── CareAgent.tsx       # Enhanced
│   │   └── types.ts
│   ├── medical/
│   │   ├── TriageResults.tsx   # Major refactor
│   │   ├── FollowupPrompt.tsx  # Enhanced
│   │   └── ProgressiveStatus.tsx # Enhanced
│   └── effects/                # New
│       └── ParticleFlow.tsx
├── styles/
│   ├── globals.css             # Cleanup
│   ├── animations.css          # New
│   └── tokens.css              # Minor updates
└── pages/
    ├── HomePage.tsx            # Simplification
    └── TriagePage.tsx          # Layout changes
```

---

## Risk Mitigation

1. **3D Performance**: Maintain fallback SVG for all new 3D components
2. **User Confusion**: A/B test simplified vs. current design
3. **Mobile Experience**: Test on real devices early
4. **Accessibility Regression**: Automated axe-core tests
5. **Algorithm Misrepresentation**: Clinical review of all new visualizations

---

## Next Steps

After approval:
1. Create new component files
2. Build components in isolation (Storybook-style)
3. Integrate into existing pages incrementally
4. Test each phase before moving to next
5. Gather user feedback continuously
