# Workshop Agenda

1. Discuss workshop goals
   - Interactive discussion around a simple example scenario that illustrates key concepts of AI Agents (specifically a multi-agent system)
   - Discuss an example you can use with your technical or non-technical customers, including C-level
     - How to present it
     - What to expect from the customer
   - A subject 99% of people will be able to relate to without a technical background

2. Discuss workshop format
   - One hour is not long enough for hands-on
   - Talk though an example and how it applies or overlays AWS AI technologies
   - Will provide all the resources for you to present to your customers (code on GitHub and GitLab)

3. Has anyone had work done around their house recently?
   - What was done? (e.g., plumbing, electrical, landscaping, etc.)
   - What types of projects were involved? (e.g., small repair, large renovation, new construction, etc.)
   - Who did the work? (contractor, tradesman, friend, family member, etc.)
   - If you used a contractor, what resources did they hire to complete the job?
   - What outside suppliers/vendors were used?
   - Did they or you need to get any permits or inspections done?
   - How long did the job take from start to finish?
   - Describe any challenges or issues that came up during the project and how they were resolved
   - Walk through a simple project example (e.g., kitchen remodel, bathroom renovation, landscaping project)

4. Introduce the example scenario
   - Residential General Contracting Company
   - Performs home renovations and new construction for residential customers
   - Manages multiple projects simultaneously, each with its own timeline, budget, and resource requirements
   - Coordinates with various subcontractors, suppliers, and clients to ensure successful project completion

5. AWS Technologies
   - Strands Agents: Strands Agents SDK empowers developers to quickly build, manage, evaluate and deploy AI-powered agents using large language models (LLMs) and generative AI.
   - Amazon Bedrock Foundation Models: Amazon Bedrock Foundation Models (LLM/VLM) provides access to leading foundation models from Anthropic, Meta, Amazon and other through a fully managed service.
   - Amazon Bedrock AgentCore: Amazon Bedrock AgentCore is an agentic platform on Bedrock for building, deploying, and operating production-grade AI agents with managed runtime, memory, policy, and observability services.
   - MCP (Model Context Protocol): MCP is an open standard from Anthropic that defines how AI applications (LLM “hosts”) connect to external tools, data sources, and prompts over a unified client–server protocol.
   - Kiro: Kiro is an agentic AI IDE from AWS that uses AI agents, specs, and hooks to help you go from prompt to production, with deep integration into AWS workflows and tooling.

6. Relate Back to AI Agents
   - The General Contractor is a primary "orchestrator agent" who handles user interaction and determines which tradespeople to "specialized agents" to call
   - The tradespeople (e.g., plumbers, electricians, carpenters) are specialized agents who perform specific tasks based on the General Contractor's instructions

7. Key Principles of a Multi-Agent Agentic System:
   - Orchestration: A controlling logic or structure to manage the flow of information and tasks between agents.
   - Specialization: An agent has a specific role or expertise, and a set of tools that it can use.
   - Collaboration: Agents communicate and share information to work upon each other's work.
   - Pattern of Interaction (Strands Agents): Swarm, Hierarchical, Graph, Workflow

8. Way to Extend this Project as a Workshop
   - Add a new specialized agent (e.g., interior designer, landscaper)
   - Introduce unexpected challenges (e.g., weather delays, budget overruns)
   - Explore different orchestration strategies (e.g., decentralized vs. centralized)
   - Use an Agentic IDE to build and deploy the multi-agent system
   - Deploy the system on AWS using Bedrock and other relevant services

9. Ways to Interact with Project Code
   - Deploy and run the project locally (what I am doing today)
   - Deploy and run the project locally using Docker (code in project repo)
   - Deploy and run the project on AWS using EC2, ECS, EKS, or Fargate  (code in project repo for ECS/Fargate)
   - Deploy and run the project using AWS Bedrock AgentCore (Runtime, Gateway, Identity, Observability, etc.)

10. Wrap Up and Next Steps
    - Provide resources for further learning and exploration
    - Encourage participants to think about how they can apply these concepts in their own contexts
    - Q&A session to address any remaining questions or concerns
