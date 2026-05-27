# UI System Guide

## Purpose

This guide defines the current visual system used across Tech Restore Desk pages so new features stay consistent.

## Design direction

- tone: practical, calm, and trustworthy for front-desk operations
- visual style: soft-card surfaces, high-contrast text, rounded controls
- interaction style: subtle lift on hover for clickable cards and clear disabled states

## Core layout patterns

- page container: center content with `maxWidth` around 1180-1280 and `width: 100%`
- primary spacing rhythm: 16px and 18px vertical gaps
- panel pattern:
  - gradient background from white to soft green tint
  - border `1px solid rgba(29, 43, 40, 0.12)`
  - border radius near 12-20px depending on component role
  - soft shadow for depth without heavy contrast
- responsive grids:
  - use `repeat(auto-fit, minmax(...))` for card and form sections
  - avoid rigid 3-column layouts that collapse poorly on narrow screens

## Color and semantic accents

- base text: dark green-charcoal for readability
- muted text: desaturated green-gray for metadata and helper text
- primary action:
  - deep green gradient button
  - pill radius with moderate shadow
- warning state:
  - warm amber background and border for policy warnings
- status badges/chips:
  - contextual tints by status where relevant (queue, inventory signals)

## Control patterns

- inputs and selects:
  - full width within container
  - 10-12px internal padding
  - 12px radius
  - neutral border with white background
- primary buttons:
  - gradient green background
  - white/off-white text
  - pill radius
  - pointer cursor and visual hover/press affordance
- secondary buttons:
  - light background with thin border
  - used for utility and quick state transitions

## Content patterns

- cards with summary + metadata:
  - title/primary value first
  - secondary metadata below in smaller muted text
- section headers:
  - concise noun phrase + optional count chip
- tables:
  - keep strong header contrast
  - use subtle row striping for scan speed
  - highlight key numeric cells with color and weight

## Motion and interaction

- hoverable cards should use:
  - slight translateY lift (1-2px)
  - increased shadow depth
  - short transitions (about 160ms)
- avoid heavy animation or delayed interactions that slow workflows

## Accessibility and readability

- keep strong contrast for body text and interactive controls
- preserve keyboard operability for all form and action controls
- avoid relying only on color to communicate status
- use visible text labels for all inputs (no placeholder-only labels)

## Current pages aligned to this guide

- app shell
- dashboard
- inventory
- donors
- queue
- hours
- tickets
- loaners
- settings
- intake
- ticket detail

## Remaining follow-up candidates

- intake and ticket-detail follow-up pass is complete for current scope
- optional future enhancement: introduce shared CSS tokens/theme variables to reduce repeated inline style objects

