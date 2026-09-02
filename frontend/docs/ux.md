# Healia — UX Specification

## 1. UX Principles

- Keep the experience simple.
- One primary action at a time.
- Minimize unnecessary steps.
- Make every screen immediately understandable.
- Keep medical information clear and easy to scan.
- Never make the user wonder what is happening.
- Always provide a clear way to continue or stop.
- Design mobile-first, then adapt for desktop.

## 2. Main Flow

```text
Landing
   ↓
Start Consultation
   ↓
Voice Consultation
   ↓
Processing
   ↓
Results
```

## 3. Landing

### Goal

Explain Healia quickly and get the user into a consultation.

### Content

- Healia logo/name
- Short description
- Short explanation of how it works
- Primary action: **Start Consultation**
- Small medical disclaimer

### Primary Action

**Start Consultation**

### Navigation

Keep navigation minimal:

- Home
- About
- Privacy

Do not add unnecessary navigation items.

---

## 4. Start Consultation

### Goal

Prepare the user before starting.

### Content

- Short explanation of the consultation
- What the user can expect
- Voice interaction explanation
- Privacy note
- Medical disclaimer

### Primary Action

**Start Consultation**

### Secondary Action

**Go Back**

The user should understand that Healia will ask questions about their symptoms before starting.

---

## 5. Voice Consultation

### Goal

Make talking to Healia feel natural and effortless.

### Main Interface

The screen should focus on the current conversation.

```text
        Healia

     [ Voice State ]

     "Listening..."

-------------------------

You:
I have had a headache
since this morning.

Healia:
Can you tell me where
the pain is located?

-------------------------

        [ End ]
```

### Voice States

Clearly communicate:

- Listening
- Thinking
- Speaking
- Ready
- Error

The visual state should change immediately when the state changes.

### Conversation

Show recent conversation/transcript without overwhelming the user.

The current interaction should always be visually dominant.

### Primary Interaction

The user should not need to type unless voice input fails or the user prefers text.

### Controls

Keep controls minimal:

- Microphone / voice control
- End consultation
- Optional text input fallback

Do not add unnecessary controls.

---

## 6. Assessment Experience

The assessment should feel like a conversation, not a medical questionnaire.

Healia should:

1. Understand the user's initial complaint.
2. Ask relevant follow-up questions.
3. Adapt questions based on previous answers.
4. Check important warning signs.
5. Collect enough information to provide useful guidance.
6. Avoid asking unnecessary questions.

The user should not see internal retrieval or reasoning.

### Assessment Status

When appropriate, show subtle progress information such as:

**Understanding your symptoms**

or

**Checking a few more details**

Avoid exposing technical terms such as:

- RAG
- embeddings
- vector search
- reranking
- LLM
- retrieval pipeline

---

## 7. Processing

### Goal

Prevent the user from thinking the application is stuck.

Show a simple status:

```text
Preparing your guidance

Reviewing your symptoms
Checking medical references
Preparing your results
```

Use progressive status updates when available.

Do not use fake progress percentages.

Do not make the user wait on an empty screen.

---

## 8. Results

### Goal

Give the user a clear understanding of what to do next.

Results should be structured and scannable.

### Order

```text
Summary
   ↓
What may be going on
   ↓
What you can do now
   ↓
Warning signs
   ↓
When to seek medical care
   ↓
Medical references
   ↓
Disclaimer
```

### Summary

Give a short plain-language summary of the user's situation.

### What May Be Going On

Present possible explanations carefully.

Do not present uncertain possibilities as confirmed diagnoses.

### What You Can Do Now

Give practical next steps.

### Warning Signs

This section must be visually prominent.

If urgent medical attention may be required, make that immediately obvious.

### Medical References

Show the sources used to support the guidance.

Keep citations readable without making the interface look academic.

Allow users to expand details when necessary.

### Disclaimer

Clearly state that Healia does not replace a qualified healthcare professional and that emergency symptoms require appropriate medical care.

---

## 9. Error States

Errors should explain what happened and what the user can do.

### Voice Error

```text
We couldn't hear you clearly.

Please try again.
```

Action:

**Try Again**

### Connection Error

```text
Your connection was interrupted.

Please check your connection and try again.
```

Action:

**Reconnect**

### Processing Error

```text
We couldn't prepare your guidance.

Please try again.
```

Action:

**Try Again**

Avoid technical error messages.

---

## 10. Empty States

Never show an unexplained empty screen.

Every empty state should answer:

1. What is happening?
2. What should the user do?

Keep empty states short.

---

## 11. Mobile UX

Mobile is a primary experience.

Requirements:

- Large touch targets
- Simple navigation
- Voice control easy to reach
- Important information visible without excessive scrolling
- Readable text
- No horizontal scrolling
- Results optimized for scanning

The consultation interface should feel natural on a phone.

---

## 12. Desktop UX

Desktop should use the additional space without becoming visually complicated.

Recommended structure:

```text
┌──────────────────────────────────────────────┐
│ Healia                         About  Privacy │
├──────────────────────────────────────────────┤
│                                              │
│        Consultation                          │
│                                              │
│              Voice State                     │
│                                              │
│        Conversation / Transcript             │
│                                              │
│              Controls                        │
│                                              │
└──────────────────────────────────────────────┘
```

Do not stretch content across the entire screen.

Keep the main content at a comfortable reading width.

---

## 13. Accessibility

- Use semantic HTML.
- Maintain sufficient color contrast.
- All controls must have accessible labels.
- Do not rely only on color to communicate state.
- Support keyboard navigation.
- Respect reduced-motion preferences.
- Make text readable at larger sizes.
- Voice controls must have a text alternative.

---

## 14. UX Rules

### Always

- Show the current state.
- Make the next action obvious.
- Keep important information prominent.
- Use plain language.
- Keep screens focused.
- Preserve the user's conversation context.

### Never

- Hide important medical warnings.
- Use unnecessary popups.
- Add unnecessary confirmation dialogs.
- Use confusing technical terminology.
- Create unnecessary pages.
- Overload the user with information.
- Make the interface look like a generic AI chatbot.
