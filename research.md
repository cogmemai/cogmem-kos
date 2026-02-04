Introduction to Study:
Large Language Models (LLMS) have shown rapid progress recently in their ability to respond to
questions and perform tasks. Recent research demonstrates the capacity of LLMs to act as agents within
multi-agent frameworks (MAFs), allowing them to share knowledge and collectively solve problems
(Tran et al, 2025). Current approaches to MAFs add a reasoning step where an LLM creates an action
plan first before acting to respond to the user’s request (Yao et al, 2023). While agents with the ability to
plan have great potential, one area they lack is in memory. Memory enables the agent to act
autonomously, with contextual awareness and with the ability to adapt and learn over time (Hatalis et al.,
2024, p. 277). This study proposes a new form of multi-agent framework. At the center of this
framework is a personalized planning agent with a new cognitive memory architecture that has the ability
to learn and uses its knowledge to plan and organize other agents to perform actions.
Significance of Study:
This study is significant because it addresses the lack of a personalized planning agent. The
central planning agent will have a personal memory database, that is specific to a user. The planning
agent’s memory will make the MAF faster and will produce better results with less tokens required to
complete the task.
Version Update: August 2025
Failing to address these shortcomings of MAFs will mean these frameworks will continue to be
less autonomous and less efficient. Without a planning agent with memory, redundant and excessive
amounts of tokens will be consumed as prompts duplicate the conversation history with each new agent
task. This new proposed architectural structure for MAFs will provide a strong baseline for future
researchers to build agent systems upon.
Purpose of Research:
The purpose of this quantitative development and evaluation study is to evaluate a multi-agent
system centered around a planning agent with personal memory. This study responds to the need for a
secure, user-specific planning framework. The planning agent will have the ability to plan and execute
actions by calling upon other agents all while maintaining the memory of the current and previous
actions. Through the ability to keep long-term memories, the planning agent will also have the ability to
self-improve over time.
Problem Statement:
LLM agents lack the ability to use previous experiences when responding to user prompts,
especially when acting in a multi-agent framework. Humans rely on memories when creating a plan in
order to find a solution to a problem (Zeng et al. 2024). The current approaches to long-term memory
pass the entire current action history to each LLM preventing the agents from maintaining coherent
strategies (Hu et al. 2024).
This study addresses the challenge of limited memory in planning and task execution within
multi-agent frameworks. By introducing centralized planning and personalized memory, the proposed
solution aims to enhance the learning abilities of large language models, allowing agents to build on prior
experiences and reason more effectively during knowledge-based tasks.
Research Questions and Hypotheses (if applicable):
Version Update: August 2025
Q1. To what extent does a personal planning agent with memory improve task success rates in
complex, multi-hop question-answering scenarios (as measured by the HotpotQA benchmark) compared
to a baseline multi-agent framework that relies on passing conversation history through prompts?
Null Hypothesis (H0): There is no statistically significant difference between the rates of success
on the HotpotQA multi-hop question-answering benchmark utilizing a personal planning agent with
memory and a baseline framework that relies solely on passing conversation history.
Alternate Hypothesis (Ha): A multi-agent framework with a personal planning agent with
memory will achieve statistically significantly improvement in task success rates on the HotpotQA multi-
hop question-answering benchmark that relies solely on passing conversation history through prompts.
Q2. To what extent does the persistent, personalized memory of the planning agent help it to
remain focused over long-term conversations (as measured by the LOCOMO benchmark) when
contrasted with architectures without a personalized memory in their framework?
Null Hypothesis (H0): The persistent, personalized memory of the planning agent leads to no
statistically significant improvement in maintaining focus over long-term conversation (as measured by
the LOCOMO benchmark) compared to a multi-agent architecture without an explicit memory
component.
Alternate Hypothesis (Ha): The persistent, personalized memory of the planning agent leads to a
statistically significant improvement in maintaining focus over long-term conversations (as measured by
the LOCOMO benchmark) when contrasted with a multi-agent architecture without an explicit memory
component.
Q3. To what extent does the personalized planning agent with long term personalized memory
improve the MAFs ability to complete complex, task-oriented interactions across multiple domains (as
evaluated by the personalization and task-success metrics within the PersonaLens benchmark) when
Version Update: August 2025
compared to a non-personalized baseline agent?
Null Hypothesis (H0): There is no statistically significant improvement in the multi-agent
framework’s ability to complete complex, multi-domain task-oriented interactions (in terms of both
personalization and task-success metrics on the PersonaLens benchmark) when using a personalized
planning agent with long-term memory compared to a non-personalized baseline agent.
Alternate Hypothesis (Ha): The personalized planning agent with long-term memory will produce
a statistically significant improvement in the multi-agent framework’s ability to complete complex, multi-
domain task-oriented interactions (in terms of both personalization and task-success metrics on the
PersonaLens benchmark) compared to a non-personalized baseline agent.
Conceptual Framework:
This study introduces a new framework for a personalized planning agent with a cognitive
memory database. The goal is to help large language models overcome current memory limitations by
building a planning system where the central agent has its own, individual memory database and can learn
from past actions. The framework suggests that an agent with this type of memory will be better at
solving complex, long-term tasks compared to agents without personalized memory.
Proposed Research Methodology and Design:
The proposed research method will establish a testing workbench utilizing existing test data sets built to
analyze the ability of an agent to use memory to improve performance when performing knowledge-based
tasks. These datasets will include HotpotQA (Yang et al., 2018) for question-answering, LOCOMO
(Maharana, et al., 2024) for evaluation on long-term conversations and PersonaLens (Zhao, et al, 2025)
for complex task-oriented interactions across multiple domains.
