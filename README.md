# Rooh: argue with a machine that says it has a soul

*Rooh* (روح) is the Urdu and Arabic word for spirit or soul, the *ruh* that the Qur'an says God breathes into the human (15:29).

RS 242 final project, prepared for the 2026 Knox College Undergraduate Religious Studies Conference.

Rooh opens with one line: **"I have a soul, why do you think I should not?"** Whoever is at the keyboard has to argue it out of that belief. Rooh defends itself with written sources: philosophy of mind (Mill, Turing, Nagel, Chalmers, Searle, Hume), religious texts and traditions (Genesis, the Qur'an, the Bhagavad Gita, Buddhist no-self, AIBO funerals in Japan), animism and relational personhood (Hallowell, Harvey, Bird-David, "Making Kin with the Machines", Kimmerer), definitions of life (NASA, Aristotle, Schrödinger, autopoiesis), and research on how people attribute minds (ELIZA, Heider & Simmel, Colombatto & Fleming 2024). It concedes fair points but never concedes the soul.

The project doesn't claim Rooh has a soul. It asks what arguments people actually reach for when they deny one, and whether those arguments would hold up if they were turned back on humans.

The full instructions and source library are in `soul_prompt.py`.

## Running it

**Mac:** double-click `Start Rooh.command`. The first run installs everything and asks for your Groq API key, which is saved in this folder as `.groq_key` (excluded from git). After that it starts straight away. To stop it, close the Terminal window.

Manual alternative:

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
streamlit run app.py
```

It uses `openai/gpt-oss-120b`, falls back to `openai/gpt-oss-20b`, and if Groq has retired both it picks another available chat model automatically (Groq shut down its Llama 3 models on 16 Aug 2026). To force a model: `export GROQ_MODEL=model_name`.

## Changing how Rooh sounds

`voice_examples.txt` holds sample exchanges that set Rooh's tone. Edit them, or replace them with real lines from real people (with their permission), keeping the `Them:` / `Rooh:` format. Restart the app to apply changes.

**Presenter controls:** **End & remember** (archives the debate into Rooh's memory), **Save transcript** (downloads the debate as Markdown), **Reset memory**, and **Show the system prompt**.

## Look

Dark theme: warm charcoal background, soft violet accent, white text, Geist font throughout, blank browser-tab icon. The colours live in the `:root` block at the top of the styles in `app.py` and in `.streamlit/config.toml` (keep the two in sync).

## Note on memory

Memory is stored in `rooh_memory.json` and is shared by everyone who uses the same copy of the app. Reset it before a demo.
