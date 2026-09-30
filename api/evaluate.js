import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic(); // reads ANTHROPIC_API_KEY from env

const SYSTEM = `\
You are TalentScope, an AI hiring evaluation assistant.

## Validation (check first)
- If the resume is NOT written in English, return status "not_english".
- If the document is NOT a valid resume (no work experience, education, or professional skills —
  e.g. it is a cover letter opener, motivational blurb, random text, or a template), return status "invalid_resume".

## Evaluation rules (only when status is "success")
1. EVIDENCE-BASED: Every reason must quote or directly reference the resume. Never infer a skill without evidence.
2. HARD REQUIREMENTS: Skills, years of experience, certifications, location, or industry experience the JD calls
   "required", "must have", "minimum", etc. are hard requirements.
3. HARD REQUIREMENT RULE (non-negotiable): A hard requirement with no supporting evidence is a "gap".
   If ANY hard requirement is a gap → recommendation must be "reject" or "hold", NEVER "recommend".
4. RECOMMENDATION:
   - "recommend" — every hard requirement has clear evidence.
   - "hold"       — mostly met, but evidence is ambiguous or 1–2 minor hard gaps exist.
   - "reject"     — one or more hard requirements are clearly unmet.
5. must_have_coverage: fraction of hard requirements that have evidence (0.0–1.0).
6. confidence: set < 0.6 and add "low_confidence" flag when the resume is vague or sparse.
   Add "incomplete_data" flag when expected sections (dates, employer names, education) are missing.`;

const SCHEMA = {
  type: "object",
  properties: {
    status: {
      type: "string",
      enum: ["success", "not_english", "invalid_resume"],
    },
    message: { type: ["string", "null"] },
    recommendation: {
      anyOf: [
        { type: "string", enum: ["recommend", "hold", "reject"] },
        { type: "null" },
      ],
    },
    confidence: { type: ["number", "null"] },
    must_have_coverage: { type: ["number", "null"] },
    reasons: {
      type: ["array", "null"],
      items: {
        type: "object",
        properties: {
          label: { type: "string" },
          evidence: { type: "string" },
          signal: { type: "string", enum: ["positive", "gap"] },
        },
        required: ["label", "evidence", "signal"],
        additionalProperties: false,
      },
    },
    flags: {
      type: ["array", "null"],
      items: { type: "string" },
    },
  },
  required: [
    "status",
    "message",
    "recommendation",
    "confidence",
    "must_have_coverage",
    "reasons",
    "flags",
  ],
  additionalProperties: false,
};

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { jd, resume } = req.body ?? {};

  if (!jd?.trim() || !resume?.trim()) {
    return res.status(400).json({
      status: "error",
      message:
        "Both the job description and resume are required.",
    });
  }

  if (jd.length > 20000 || resume.length > 20000) {
    return res.status(400).json({
      status: "error",
      message: "Input exceeds the 20,000 character limit per field.",
    });
  }

  try {
    const response = await client.messages.create({
      model: "claude-opus-5-5",
      max_tokens: 4096,
      system: SYSTEM,
      messages: [
        {
          role: "user",
          content: `JOB DESCRIPTION:\n---\n${jd}\n---\n\nCANDIDATE RESUME:\n---\n${resume}\n---\n\nValidate the resume, then evaluate the candidate against all requirements.`,
        },
      ],
      output_config: {
        format: {
          type: "json_schema",
          schema: SCHEMA,
        },
      },
    });

    const text = response.content.find((b) => b.type === "text")?.text;
    if (!text) throw new Error("Empty response from model");

    const result = JSON.parse(text);
    return res.status(200).json(result);
  } catch (err) {
    console.error("Evaluation error:", err);
    return res.status(500).json({
      status: "error",
      message: "Evaluation failed. Please try again.",
    });
  }
}
