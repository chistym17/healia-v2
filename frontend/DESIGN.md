# Healia — Design System

## 1. Design Direction

Healia should look like a **calm, modern clinical product**.

The visual style should be:

- Simple
- Classy
- Clean
- Warm
- Professional
- Trustworthy
- Spacious
- Human

Avoid the typical AI-product aesthetic.

## 2. Color System

### Background

Primary background:

`#F8F8F5`

Secondary background:

`#FFFFFF`

### Text

Primary text:

`#17201D`

Secondary text:

`#5F6965`

Muted text:

`#87918D`

### Brand

Primary brand:

`#155E59`

Dark brand:

`#104944`

Light brand:

`#E6F1EF`

### Borders

Default border:

`#DDE3E0`

Subtle border:

`#E9EDEB`

### Status

Success:

`#2F6F55`

Warning:

`#9A6A20`

Danger:

`#B54747`

Information:

`#356A82`

Do not use gradients.

Do not use purple or indigo as primary brand colors.

## 3. Typography

Use one clean sans-serif font family throughout the application.

Preferred:

**Inter**

Fallback:

`system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

### Scale

Page title:

`40–48px`

Section heading:

`28–32px`

Subheading:

`20–24px`

Body:

`16px`

Small text:

`14px`

Caption:

`12–13px`

### Rules

- Use comfortable line height.
- Avoid excessively large headings.
- Avoid bolding everything.
- Use font weight to create hierarchy.
- Body text should normally be `400`.
- Important headings should normally be `600`.

## 4. Layout

Use generous whitespace.

Maximum content width:

`1200px`

Reading/content width:

`720–800px`

Primary consultation width:

`800–960px`

Use consistent horizontal padding:

Mobile:

`20px`

Tablet:

`32px`

Desktop:

`40–48px`

## 5. Spacing

Use a consistent spacing scale:

```text id="lzzrbt"
4px
8px
12px
16px
24px
32px
40px
48px
64px
80px
```

Prefer fewer, larger spacing decisions rather than many arbitrary values.

## 6. Border Radius

Use moderate rounding.

Small:

`6px`

Default:

`8px`

Large:

`12px`

Avoid excessive pill-shaped UI.

Pills should only be used for:

- Status indicators
- Small tags
- Compact metadata

Buttons should normally use `8px` radius.

Cards should normally use `12px` radius.

## 7. Shadows

Use shadows very sparingly.

Default:

No shadow.

If elevation is required, use a very subtle shadow.

The interface should primarily use:

- Background contrast
- Borders
- Spacing

rather than heavy shadows.

## 8. Buttons

### Primary Button

Use the deep teal brand color.

Characteristics:

- Clear
- Solid
- Medium height
- Moderate radius
- Strong readable text

Example:

**Start Consultation**

### Secondary Button

Use a white/off-white background with a border.

Example:

**Learn More**

### Text Button

Use for low-priority actions.

Example:

**Go Back**

### Rules

- One primary button per section.
- Do not use multiple competing primary buttons.
- Buttons should have clear action labels.
- Avoid overly rounded buttons.

## 9. Navigation

Keep navigation minimal.

Desktop:

```text id="t6b0k2"
Healia                         About   Privacy
```

Mobile:

```text id="n1n4k3"
Healia                         Menu
```

The logo should be simple and text-based unless a strong custom mark is designed later.

Avoid large decorative navigation.

## 10. Cards

Cards should be used only when they improve information grouping.

Good uses:

- Medical warning
- Result section
- Reference
- Important information

Avoid:

```text id="6h2xk9"
Card
 ├── Icon
 ├── Heading
 ├── Description
 └── Button
```

repeated across the page.

Do not turn every section into a card.

## 11. Forms

Inputs should be:

- Clearly labeled
- Spacious
- Easy to read
- Border-based
- Moderately rounded

Avoid floating labels unless necessary.

Use clear error messages below the relevant field.

## 12. Voice Interface

The voice interface is a central part of Healia.

Keep it visually calm.

### Voice State

Use a simple central visual element.

Possible states:

```text id="e7uk8m"
Listening
Thinking
Speaking
Ready
Error
```

The state should be communicated using:

- Shape
- Subtle movement
- Text
- Small status indicator

Do not use a giant glowing orb.

Do not use neon effects.

Do not use excessive animation.

### Main Voice Area

The user should immediately understand:

**What Healia is doing right now.**

Example:

```text id="l2j8x0"
             Listening

        [ simple voice visual ]

      Tell me what you're feeling
```

## 13. Conversation

Conversation should be visually quiet.

User messages and Healia messages should be easy to distinguish without creating a typical ChatGPT-style interface.

Avoid excessive message bubbles.

Use spacing and typography to establish hierarchy.

## 14. Processing Screen

Keep it minimal.

Example:

```text id="y0n8k3"
Preparing your guidance

✓ Reviewing your symptoms
✓ Checking medical references
○ Preparing your results
```

Use subtle motion only where useful.

Never use fake percentages.

## 15. Results

Results should prioritize readability.

Recommended structure:

```text id="1p7d4a"
Your health guidance

Summary
────────────────────

What may be going on
────────────────────

What you can do now
────────────────────

Warning signs
────────────────────

When to seek medical care
────────────────────

References
────────────────────
```

Use clear headings and spacing rather than putting every section inside a card.

## 16. Warning Messages

Medical warnings should be visually distinct.

Use a light background, border, icon, and strong heading.

Example:

```text id="6v9xq2"
Warning

Seek urgent medical attention if you
experience severe chest pain, difficulty
breathing, or loss of consciousness.
```

Do not rely only on red text.

## 17. References

References should be secondary to the guidance.

Show:

- Source name
- Relevant title
- Optional short description
- Link when appropriate

Allow references to expand if more detail is available.

Do not make the results page look like a research paper.

## 18. Disclaimer

Keep the disclaimer visible but visually secondary.

Use smaller text and muted styling.

It should never compete with the actual guidance.

## 19. Icons

Use icons sparingly.

Icons should communicate meaning, not decoration.

Preferred style:

- Simple
- Outline-based
- Consistent stroke width

Do not place an icon beside every heading.

## 20. Animation

Animation should be subtle and purposeful.

Allowed:

- Voice state transitions
- Button hover/focus
- Loading states
- Small page transitions

Avoid:

- Large entrance animations
- Floating elements
- Parallax
- Bouncing UI
- Constant movement
- Decorative animations

Respect `prefers-reduced-motion`.

## 21. Responsive Design

Design for mobile first.

### Mobile

- Single column
- Large touch targets
- Minimal navigation
- Full-width primary actions where appropriate
- Comfortable text size

### Desktop

- Center the main content
- Use additional whitespace
- Keep reading width controlled
- Use side panels only when they provide real value

Do not simply stretch the mobile layout across the desktop screen.

## 22. Accessibility

All components must:

- Have visible focus states
- Meet accessible contrast requirements
- Support keyboard navigation
- Have accessible labels
- Use semantic HTML
- Avoid color-only status communication
- Support reduced motion

## 23. Forbidden Design Patterns

Do not use:

- Purple AI gradients
- Blue/purple neon gradients
- Glassmorphism
- Excessive shadows
- Giant hero text
- Giant glowing AI orb
- Excessive rounded cards
- Three-column feature-card layouts
- Decorative AI illustrations
- Excessive badges
- Excessive pills
- Fake testimonials
- Stock medical imagery
- Unnecessary animations
- Dark futuristic AI dashboards
- Excessive whitespace that makes the product feel empty
- Every section inside a card
- Every heading with an icon

## 24. Core Rule

When choosing between:

**more decoration**

and

**more clarity**

choose **clarity**.

Healia should feel like a product users can trust with something important.
