# General Contractor as an Analogy for Orchestration Agents

## Project Description

This agentic training workshop demonstrates orchestration patterns using the analogy of a general contractor. The general contractor serves as the primary orchestration agent, coordinating and delegating work to specialized agents representing different trades: Carpenter, Electrician, Mason, Plumber, and others. Materials and resources for these jobs are sourced through MCP (Model Context Protocol) servers, which act as external service providers. This framework illustrates how complex, multi-agent systems can be designed to mirror real-world project management and coordination.

## General Analogy Overview

- **General Contractor:** The central agent responsible for orchestrating complex projects, delegating tasks, and ensuring project completion.
- **Specialist Agents (Resources):** Expert agents (Carpenter, Electrician, Mason, Plumber, etc.) each specializing in a domain and reporting progress/outcomes to the contractor.
- **Material Providers (MCP Servers):** External resources or APIs supplying inputs/materials/tools as needed.

## Core Specialist Agent Roles

- **Architect Agent:** Designs project plans, blueprints, and specifications.
- **Carpenter Agent:** Handles construction of walls, doors, cabinetry, trim.
- **Electrician Agent:** Installs, repairs, and upgrades electrical systems.
- **Plumber Agent:** Installs, connects, and troubleshoots water/gas lines.
- **Mason Agent:** Builds with stone, brick, and concrete.
- **Painter Agent:** Finishes surfaces, may also advise on color/design.
- **HVAC Agent:** Installs and maintains heating, ventilation, and cooling systems.
- **Roofer Agent:** Installs and repairs roof structures.
- **Landscaper Agent:** Handles exterior land and plant work.

## MCP Servers (Material Sourcing Agents)

- **Lumber Supplier MCP:** Provides wood and framing materials.
- **Electrical Supply MCP:** Cables, fixtures, circuit breakers, smart home tech.
- **Plumbing Supply MCP:** Pipes, fittings, fixtures.
- **Masonry Supply MCP:** Bricks, blocks, rebar, cement.
- **Paint Supplier MCP:** Paints, primers, application tools.
- **Appliance Vendor MCP:** Stoves, refrigerators, bath/kitchen appliances.
- **Permitting MCP:** Acquires necessary permits/inspections for compliance.

Alternately, a single Construction Supply MCP could handle all material requests.

- **Building Materials Supplier MCP:** A unified supplier that can provide any construction materials (lumber, electrical, plumbing, masonry, paint, etc.) based on what's requested by agents

## Orchestration and Delegation Logic

- **Task Sequencing:** Determines correct order, e.g., framing before electrical/plumbing, inspection before closing walls.
- **Dependency Management:** Ensures no agent acts out of turn (e.g., plumber must wait for framing to finish).
- **Resource Allocation:** Assigns jobs based on agent availability/capacity.
- **Quality Assurance:** Receives reports, requests corrections, enforces standards.
- **Exception Handling:** Reacts to schedule slips, failed inspections, missing materials.

## Additional Considerations

### Communication & Coordination

- **Protocols:** How agents communicate intermediate/final results, errors, and requests for materials or clarification.
- **State Awareness:** Each agent’s awareness of project phase, dependencies, and changes.
- **Audit Trail:** Systematic logging of actions, handoffs, and decisions.

### Optimization & Flexibility

- **Dynamic Agent Selection:** Ability to swap in/out resource agents based on expertise or workload.
- **Parallelization:** Routing independent tasks to different agents simultaneously.
- **Fallback/Backup:** Redundant agents in case of failure or unavailability.

### Compliance & Governance

- **Permits/Inspections:** Ensuring agents check compliance checkpoints at defined stages, submitting requests to Permitting MCP.
- **Budget Monitoring:** Contractor oversees cost control, querying MCP servers for real-time prices.

### Monitoring & Reporting

- **Progress Tracking:** Contractor gathers regular updates for a unified project dashboard.
- **Bottleneck Detection:** Identifies where delays occur and mitigates.

### Security & Access Control

- **Credential Management:** Some jobs (e.g., electrical work) require special qualifications; Contractor checks agent profiles.
- **Material Authorization:** Contractor ensures only authorized agents can request/receive materials from MCPs.

## Agentic System Design Takeaways

- Agent orchestration requires careful modeling of specialized expertise, dependencies, and real-world logistical constraints.
- MCP servers function as programmatic APIs for material acquisition, provider integration, or information lookups.
- Realistic project flow benefits from event-driven communication, dynamic agent assignment, and robust error handling.

## Common Residential Projects

A general contractor is typically hired for a variety of residential projects, ranging from new builds to extensive renovations and upgrades. Common residential projects include:

### Home Construction and Additions

- Building custom single-family homes from the ground up.
- Constructing home additions such as extra bedrooms, attached garages, or sunrooms.

### Major Renovations and Remodels

- Full home renovations, including gutting and rebuilding interiors.
- Kitchen remodels, which often involve new cabinetry, countertops, appliance installations, and flooring.
- Bathroom renovations that may include reconfiguring layouts, replacing fixtures, and updating plumbing and electrical systems.
- Basement finishing or attic conversions to create new living spaces.
- Converting garages into accessory dwelling units (ADUs) or additional living space.

### Exterior and Structural Projects

- Building or repairing decks, patios, and porches for outdoor living.
- Roof replacement or major roof repairs.
- Exterior siding and window replacements.

### Specialized and Green Projects

- Building modular homes, pool houses, or greenhouses.
- Enhancements to energy efficiency, such as insulation or solar panel installation, as part of green building initiatives.
- Waterproofing basements and undertaking repairs for fire, water, or storm damage.

### Smaller Scale and Maintenance Projects

- General repairs and maintenance (e.g., fixing old townhouses, minor refurbishments).
- Emergency restoration services after accidents or disasters.

A general contractor is typically hired for a variety of residential projects, ranging from new builds to extensive renovations and upgrades. Common residential projects include:

## Major Task "Tools" by Specialized Agent

Modeling each tool as a major task makes the agent interaction logical and instructive: highlighting autonomy, specialization, and the importance of orchestration in a multi-agent system.

### Why mid-level granularity?

- Reflects real-world delegation by a general contractor: Each sub-agent can accept, plan, and produce a result for a known scope.
- Enables monitoring, error handling, and progress tracking at a meaningful level.
- Shows clear separation between resource allocation (tools/materials from MCP servers) and task execution (agent’s specialized expertise).

### Tasks

Here are the major task "tools" for specialized agents, listed by agent role:

- **Carpenter:**

  - Frame walls
  - Install doors
  - Build cabinets
  - Install wood flooring
  - Hang drywall
  - Build stairs

- **Electrician:**

  - Wire outlets/switches
  - Install lighting fixtures
  - Upgrade electrical panel
  - Run new circuits
  - Install ceiling fans
  - Troubleshoot wiring

- **Plumber:**

  - Install bathroom/kitchen sink
  - Connect/disconnect toilets
  - Install showers
  - Repair or replace pipes
  - Unclog drains
  - Set water heaters

- **Mason:**

  - Lay brick or stone walls
  - Pour concrete foundation or slab
  - Repair masonry
  - Install pavers
  - Build fireplaces

- **Painter:**

  - Paint interior walls and ceilings
  - Paint exterior siding
  - Prime surfaces
  - Remove old paint
  - Refinish cabinets
  - Apply wallpaper

- **HVAC:**

  - Install or repair heating systems
  - Install or repair AC units
  - Clean or replace ductwork
  - Set up thermostats
  - Perform seasonal servicing

- **Roofer:**
  - Install or replace shingles
  - Repair leaks
  - Flashing/eaves installation
  - Replace underlayment
  - Clean or repair gutters
  - Inspect roof

Each action represents a key work unit that demonstrates both specialized agent autonomy and the orchestration role of a general contractor in an agentic system. Each item represents a discrete, meaningful unit of professional work that directly showcases both the specialization and autonomy of the agent in a coordinated project orchestration scenario. This structure allows project monitoring, error handling, and cross-agent dependencies to be demonstrated clearly, supporting practical and instructive agentic training.

## Project Specifications

Based on this Project Outline, construct a modular multi-agent system that models the general contractor orchestration analogy. The system should follow these specifications:

- The backend must be implemented in Python 3.13 and use uv as the package manager.
- The frontend must be implemented in AWS Cloudscape React framework and use npm as the package manager.
- The frontend and backend should communicate via RESTful APIs.
- The frontend should provide a dashboard to monitor project progress, agent status, and material requests.
- The frontend should allow users to initiate new projects and view detailed reports.
- There should be a TOML file created by uv that defines the project dependencies for the backend.
- The backend should use the [Strands Agents](https://strandsagents.com/latest/) framework and [Python SDK](https://github.com/strands-agents/sdk-python)
- A General Contractor agent that orchestrates the overall project, delegating tasks to specialized agents and managing dependencies.
- Eight (8) specialized agents for each of the following trades: Architect, Carpenter, Electrician, Plumber, Mason, Painter, HVAC, and Roofer.
- Specialized agents can accept tasks, execute them, and report progress back to the General Contractor.
- Two (2) MCP servers that simulate material sourcing, providing necessary materials and tools as requested by the specialized agents: Building Materials Supplier MCP and Permitting MCP.
- Logic for task sequencing, dependency management, resource allocation, quality assurance, and exception handling.
- Communication protocols for agents to report progress, request materials, and handle errors.
- Monitoring and reporting mechanisms for tracking project progress and identifying bottlenecks.
- Tools for the specialized agents that represent major tasks they can perform, as outlined in the "Major Task "Tools" by Specialized Agent" section.
- Ensure compliance with permits and inspections through the Permitting MCP.
- Implement dynamic agent selection, parallelization of independent tasks, and fallback mechanisms for agent unavailability.
- Include security and access control measures for credential management and material authorization.
- Provide thorough documentation of the system architecture, agent roles, communication protocols, and orchestration logic.
