from app.schemas.coach import ActionItem, AdherenceWeek, ChurnRisk


def rank_action_items(
    member_id: str,
    member_name: str,
    adherence_weeks: list[AdherenceWeek],
    churn_risk: ChurnRisk,
) -> list[ActionItem]:
    items: list[ActionItem] = []

    if churn_risk.level == "high":
        items.append(ActionItem(
            priority="high",
            member_id=member_id,
            member_name=member_name,
            reason=f"High churn risk: {'; '.join(churn_risk.reasons)}",
            context={"churn_level": churn_risk.level, "churn_reasons": churn_risk.reasons},
        ))

    if adherence_weeks:
        latest = adherence_weeks[-1]
        if latest.pct < 50:
            items.append(ActionItem(
                priority="high",
                member_id=member_id,
                member_name=member_name,
                reason=f"Low adherence this week: {latest.pct}% (week of {latest.week_of})",
                context={"week_of": latest.week_of, "adherence_pct": latest.pct},
            ))
        elif latest.pct < 70:
            items.append(ActionItem(
                priority="medium",
                member_id=member_id,
                member_name=member_name,
                reason=f"Below-target adherence this week: {latest.pct}% (week of {latest.week_of})",
                context={"week_of": latest.week_of, "adherence_pct": latest.pct},
            ))

    # Sort: high > medium > low
    order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda x: order.get(x.priority, 3))
    return items
