# GOVERNANCE

## Overview

The odmlib project follows a lightweight governance model designed to balance:

* High-quality open-source development
* Strong alignment with CDISC standards
* Inclusive participation from both developers and domain experts

Because odmlib operates in a regulated, standards-driven space, **correctness and standards compliance take precedence 
over speed**.

---

## Guiding Principles

1. **Correctness over velocity**
   Changes must align with CDISC standards and real-world usage.

2. **Domain expertise is first-class**
   Contributions from clinical and standards experts are as important as code.

3. **Open participation, trusted review**
   Anyone can contribute; trusted roles ensure quality and consistency.

4. **Transparency in decision-making**
   Discussions and decisions should be visible and documented when possible.

5. **Usefulness for real use cases**
   Projects should be useful in real-world scenarios.
   Project goals should be clear and achievable.

---

## Roles

### Maintainers

Maintainers are responsible for the overall direction and health of the project.

**Responsibilities:**

* Define roadmap and priorities
* Make final decisions on complex or disputed changes
* Ensure architectural consistency
* Manage releases
* Oversee governance and role assignments

**Authority:**

* Have authority on all project decisions
* May override other roles when necessary, but should seek consensus

---

### Reviewers

Reviewers are trusted contributors who ensure code quality and consistency.

**Responsibilities:**

* Review pull requests for:

  * Code quality
  * Test coverage
  * API design and consistency
* Provide constructive feedback
* Approve changes for merge (non-domain-critical)

**Authority:**

* Can approve and merge non-domain-critical changes
* Collaborate with Domain Stewards on standards-related changes

---

### Domain Stewards

Domain Stewards are experts in CDISC, Define-XML, and clinical metadata standards.

**Responsibilities:**

* Review changes affecting:

  * Define-XML generation
  * ODM modeling
  * Standards compliance
* Validate correctness against:

  * CDISC specifications
  * Real-world submission practices
* Provide authoritative interpretation where specifications are ambiguous

**Authority:**

* Required approvers for any standards-related changes
* Can block changes that compromise correctness or compliance

**Note:**
Domain Stewards are not required to contribute code.

---

### Contributors

Contributors are individuals who make meaningful contributions to the project.

**Examples:**

* Code contributions
* Model contributions
* Documentation improvements
* Bug reports with actionable detail
* Feature suggestions
* Domain expertise and validation

Contributors may progress into Reviewer or Domain Steward roles over time.

See `CONTRIBUTING.md` for more details.

---

### Community

The broader community includes users and supporters of odmlib.

**Role:**

* Provide feedback
* Report issues
* Share real-world usage insights
* Help grow adoption

---

## Decision-Making Process

### Non-Domain Changes

Examples:

* Refactoring
* Performance improvements
* Tooling or infrastructure updates

**Requirements:**

* Approval from at least one Reviewer

---

### Domain-Sensitive Changes

Examples:

* Define-XML structure or generation logic
* ODM modeling decisions
* Standards interpretation

**Requirements:**

* Approval from:

  * At least one Reviewer
  * At least one Domain Steward

---

### Major Changes

Examples:

* Breaking API changes
* Significant architectural changes
* New interpretations of CDISC standards

**Requirements:**

* Discussion with the community
* Involvement of:

  * At least one Maintainer
  * At least one Domain Steward
* Consensus is preferred

---

## Role Progression

odmlib encourages contributors to grow into leadership roles.

### Contributor → Reviewer

* Multiple high-quality contributions
* Demonstrated understanding of the codebase
* Consistent, constructive participation in reviews

---

### Contributor → Domain Steward

* Demonstrated expertise in CDISC or clinical data standards
* Meaningful input on standards-related discussions
* Trusted judgment on correctness and compliance

---

### Reviewer or Domain Steward → Maintainer

* Sustained, high-impact contributions
* Leadership in technical or domain discussions
* Ability to make balanced, project-level decisions

---

## Contribution Standards

All contributions are evaluated based on their ability to:

* Improve functionality
* Enhance usability
* Ensure correctness
* Strengthen alignment with CDISC standards

See `CONTRIBUTING.md` for the full contribution rubric.

---

## Conflict Resolution

In the event of disagreement:

1. Attempt resolution through open discussion
2. Seek input from additional Reviewers or Domain Stewards
3. Maintainers make the final decision if consensus cannot be reached

---

## Governance Evolution

This governance model is intentionally lightweight and will evolve as the project grows.

Changes may be proposed via:

* Issues
* Pull requests
* Community discussion

Initially, the Core Maintainers have the authority to make decisions without reviews from other roles. As the project 
matures, the proposed decision-making process will be implemented and refined.

Note, that many of the odmlib contributors are both developers and domain experts, so they may perform both roles.

---

## Summary

odmlib’s governance model is designed to:

* Encourage broad participation
* Maintain high technical and domain quality
* Recognize the importance of clinical standards expertise

By combining open-source practices with domain-driven review, the project aims to build trustworthy, standards-aligned 
tooling for the clinical research community.
