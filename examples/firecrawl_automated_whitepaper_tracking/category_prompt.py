"""
This file defines the DESIRED_CATEGORY as a single, long string
that describes the category of interest.
"""

DESIRED_CATEGORY = """
**Definition of “AI Agents”**
An "AI Agent" is any system in which a large language model (LLM):
    1. Maintains Dynamic Control over how tasks are accomplished, including
       which tools or APIs are used and in what sequence.
    2. Plans, Reasons, and Adapts its approach based on user goals and
       feedback from its environment (e.g., tool outputs, code execution,
       external data).
    3. Acts Autonomously or Semi-Autonomously in open-ended or complex tasks
       that cannot be fully decomposed in advance.
    4. Demonstrates Decision-Making beyond hardcoded or strictly
       human-defined workflow paths, such as deciding what to do next at
       each step (versus executing a single, fixed script).

**Core Criterion for Classification**
A white paper belongs to the “AI Agents” category if its primary focus
describes, evaluates, measures, or demonstrates LLM-based systems that
exhibit or aim to exhibit one or more of the above qualities. This includes
systems that:
    • Show Partial, Incremental, or Full Autonomy in real-world or
      simulated tasks.
    • Employ LLMs to Dynamically Decide how to use tools (e.g., web
      browsing, code writing, system commands).
    • Investigate, Benchmark, or Compare the performance of such agentic
      systems, even if only a subset of tasks is completed autonomously.
    • Provide Frameworks for Building or Testing agentic capabilities in
      LLMs (e.g., multi-step planning, chain-of-thought reasoning,
      environment/tool usage).

**Clarifications to Prevent Underclassification**
    • Partial Autonomy Counts: Papers need not demonstrate 100% autonomous
      task completion. Even if an LLM handles only a fraction of tasks
      without human intervention, it can still qualify if the system’s
      goal or design involves adaptive or autonomous capabilities.
    • Research or Benchmarking is Included: Papers that focus on measuring,
      experimenting with, or benchmarking LLM agents should be classified
      as “AI Agents” if they revolve around agentic behavior, even if the
      research finds current systems are limited or only partially
      successful.
    • Use of Tools or Environment: If the paper describes LLMs selecting
      and executing code, commands, or API calls at their own discretion
      (i.e., not merely a single-step prompt for code generation), it
      likely falls under agentic systems.
    • Evaluation of Agent Performance: Studies that assess the
      effectiveness, reliability, or scalability of AI agents in performing
      tasks should be included if they address the agent’s ability to
      autonomously manage and execute tasks.
    • Integration with External Systems: Papers that explore how AI agents
      interact with external systems, databases, or APIs to accomplish
      tasks should be considered relevant.

**Exclusion Criterion**
A paper should not be classified under “AI Agents” if it only:
    • Discusses Static or Single-Step LLM Prompts that generate answers,
      translations, or content without autonomy or iterative
      decision-making.
    • Describes Purely Human-Orchestrated Pipelines where the LLM’s role is
      strictly predefined at each step (no dynamic path-finding, tool
      selection, or open-ended planning).
    • Focuses on General LLM Usage (e.g., chatbots, Q&A systems) without
      discussing autonomy, adaptive behavior, or iterative tool usage.

**Likely Categories for Agentic Systems Papers**
Based on Anthropic’s blog post, these arXiv categories are the most likely
homes for papers on agentic LLM systems:
    • Multiagent Systems (cs.MA) – Most directly relevant
    • Artificial Intelligence (cs.AI)
    • Computation and Language (cs.CL)
    • Machine Learning (cs.LG)
    • Human-Computer Interaction (cs.HC)
    • Software Engineering (cs.SE)

**Rationale for These Improvements**
1. **Enhanced Clarity on Benchmarking and Evaluation**
   The updated directives explicitly include papers that benchmark or
   evaluate AI agents, ensuring that studies like “TheAgentCompany” are
   recognized as relevant even if they focus on assessing agent performance
   rather than developing new agent architectures.
2. **Broader Inclusion of Agentic Behaviors**
   By emphasizing not only the implementation but also the evaluation and
   interaction of AI agents with external systems, the directives now cover
   a wider range of agent-focused research.
3. **Explicit Mention of Evaluation Metrics**
   Including criteria related to the effectiveness, reliability, and
   scalability of AI agents helps capture papers that analyze how well
   agents perform tasks autonomously.
4. **Integration with External Systems**
   Highlighting the interaction between AI agents and external systems
   ensures that papers discussing agents’ ability to utilize tools and APIs
   are appropriately classified.
5. **Avoidance of Specific Examples**
   The directives maintain generality by avoiding specific examples,
   ensuring they are broadly applicable to various types of agent-related
   research.
"""