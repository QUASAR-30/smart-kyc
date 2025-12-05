"""
SmartKYC - TrustScore Demo
Demonstration script showing different merchant profiles and their TrustScores
"""

import sys
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

from app.services.trustscore_calculator import calculate_trustscore_for_merchant


def print_header(title):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_trustscore_summary(merchant_name, merchant_id, result):
    """Print a clean summary of TrustScore results"""
    print(f"\n🏢 {merchant_name}")
    print(f"   ID: {merchant_id}")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Main score
    badge_emoji = {
        'PLATINUM': '🥇',
        'GOLD': '🥇',
        'SILVER': '🥈',
        'BRONZE': '🥉',
        'NONE': '⚪'
    }

    print(f"   📊 TrustScore: {result['trustscore']}/1000")
    print(f"   {badge_emoji.get(result['badge'], '⚪')} Badge: {result['badge']}")
    print(f"   ⚙️  Mode: {result['calculation_mode']}")

    # Metrics summary
    if result['calculation_mode'] == 'NORMAL':
        metrics = result['metrics']
        print(f"\n   📈 Composantes:")
        print(f"      Documents    (10%): {metrics['documents']['score']:>5.1f}/100  [{metrics['documents']['verified_count']}/5 docs]")
        print(f"      Historique   (40%): {metrics['historique']['score']:>5.1f}/100  [{metrics['historique']['anciennete']['months']} mois]")
        print(f"      Comportement (30%): {metrics['comportement']['score']:>5.1f}/100  [{metrics['comportement']['fidelisation']['recurring_pct']:.0%} récurrents]")
        print(f"      Financiers   (20%): {metrics['financiers']['score']:>5.1f}/100  [{metrics['financiers']['ca_mensuel']['amount']/1_000_000:.1f}M FCFA/mois]")

        # Recommendations
        recommendations = get_recommendations(result)
        if recommendations:
            print(f"\n   💡 Recommandations:")
            for rec in recommendations:
                print(f"      • {rec}")
    else:
        # COLD_START mode
        metrics = result['metrics']
        print(f"\n   📄 Documents vérifiés: {metrics['documents']['total_verified']}/5")
        print(f"   ⏳ Historique insuffisant (< 3 mois)")
        print(f"   📌 Score plafonné à 500 (Badge Bronze max)")


def get_recommendations(result):
    """Generate recommendations based on TrustScore analysis"""
    recommendations = []
    metrics = result['metrics']

    # Documents
    if metrics['documents']['score'] < 80:
        missing = len(metrics['documents']['missing_types'])
        recommendations.append(f"Ajouter {missing} document(s) manquant(s) pour améliorer le score")

    # Historique - Régularité
    cv = metrics['historique']['regularite']['cv']
    if cv > 0.20:
        recommendations.append(f"Améliorer la régularité des ventes (CV actuel: {cv:.1%})")

    # Comportement - Diversification
    top_customer = metrics['comportement']['diversification']['top_customer_pct']
    if top_customer > 0.20:
        recommendations.append(f"Diversifier la base client (top client: {top_customer:.1%} du CA)")

    # Financiers - Marge
    marge = metrics['financiers']['marge_brute']['percentage']
    if marge < 25:
        recommendations.append(f"Optimiser la marge brute (actuelle: {marge:.1f}%)")

    # Financiers - Rotation stock
    rotation = metrics['financiers']['rotation_stock']['times_per_year']
    if rotation < 8:
        recommendations.append(f"Améliorer la rotation du stock (actuelle: {rotation:.1f}×/an)")

    return recommendations


def demo_merchant_profiles():
    """Demo with 5 different merchant profiles"""
    print_header("SmartKYC - Démonstration TrustScore")
    print("\nCe script calcule le TrustScore pour 5 profils marchands différents.")
    print("Les données sont générées de manière reproductible par GenukaAPIClientMock.")

    merchants = [
        ("Kouassi Distribution", "kouassi-distribution", "Grand commerce alimentaire établi"),
        ("Marie Import-Export", "marie-import-export", "Commerce de gros en construction"),
        ("Abdou Trading", "abdou-trading", "Petit commerce électronique"),
        ("Jean Nouveau", "jean-nouveau-merchant", "Nouveau marchand pharmacie"),
        ("Sarah Premium", "sarah-premium-business", "Commerce textile premium"),
    ]

    for name, merchant_id, description in merchants:
        print_header(description)
        result = calculate_trustscore_for_merchant(merchant_id)
        print_trustscore_summary(name, merchant_id, result)

    # Summary table
    print_header("Tableau Récapitulatif")
    print(f"\n{'Marchand':<25} {'Score':<10} {'Badge':<12} {'Mode':<12}")
    print("─" * 80)

    for name, merchant_id, _ in merchants:
        result = calculate_trustscore_for_merchant(merchant_id)
        print(f"{name:<25} {result['trustscore']:<10} {result['badge']:<12} {result['calculation_mode']:<12}")

    print("\n")


def demo_score_breakdown():
    """Detailed breakdown of score calculation for one merchant"""
    print_header("Analyse Détaillée - Kouassi Distribution")

    merchant_id = "kouassi-distribution"
    result = calculate_trustscore_for_merchant(merchant_id)

    if result['calculation_mode'] == 'NORMAL':
        metrics = result['metrics']

        print(f"\n📊 TrustScore Final: {result['trustscore']}/1000")
        print(f"🏅 Badge: {result['badge']}\n")

        # Documents
        print("1️⃣  DOCUMENTS (Poids: 10%)")
        doc = metrics['documents']
        print(f"   Score: {doc['score']:.1f}/100")
        print(f"   Vérifiés: {', '.join(doc['verified_types'])}")
        print(f"   Manquants: {', '.join(doc['missing_types']) if doc['missing_types'] else 'Aucun'}")
        print(f"   Contribution au score: {doc['score'] * 0.10 * 10:.0f} points\n")

        # Historique
        print("2️⃣  HISTORIQUE BUSINESS (Poids: 40%)")
        hist = metrics['historique']
        print(f"   Score global: {hist['score']:.1f}/100")
        print(f"   ├─ Ancienneté: {hist['anciennete']['score']}/100 ({hist['anciennete']['months']} mois)")
        print(f"   ├─ Régularité: {hist['regularite']['score']}/100 (CV: {hist['regularite']['cv']:.1%})")
        print(f"   └─ Croissance: {hist['croissance']['score']}/100 ({hist['croissance']['monthly_growth_rate']:.1%}/mois)")
        print(f"   Contribution au score: {hist['score'] * 0.40 * 10:.0f} points\n")

        # Comportement
        print("3️⃣  COMPORTEMENT CLIENT (Poids: 30%)")
        comp = metrics['comportement']
        print(f"   Score global: {comp['score']:.1f}/100")
        print(f"   ├─ Diversification: {comp['diversification']['score']}/100 (Top: {comp['diversification']['top_customer_pct']:.1%})")
        print(f"   ├─ Fidélisation: {comp['fidelisation']['score']}/100 (Récurrents: {comp['fidelisation']['recurring_pct']:.1%})")
        print(f"   └─ Panier moyen: {comp['panier_moyen']['score']}/100 (Tendance: {comp['panier_moyen']['trend']:+.1%})")
        print(f"   Contribution au score: {comp['score'] * 0.30 * 10:.0f} points\n")

        # Financiers
        print("4️⃣  FINANCIERS (Poids: 20%)")
        fin = metrics['financiers']
        print(f"   Score global: {fin['score']:.1f}/100")
        print(f"   ├─ CA mensuel: {fin['ca_mensuel']['score']}/100 ({fin['ca_mensuel']['amount']/1_000_000:.1f}M FCFA)")
        print(f"   ├─ Rotation stock: {fin['rotation_stock']['score']}/100 ({fin['rotation_stock']['times_per_year']:.1f}×/an)")
        print(f"   └─ Marge brute: {fin['marge_brute']['score']}/100 ({fin['marge_brute']['percentage']:.1f}%)")
        print(f"   Contribution au score: {fin['score'] * 0.20 * 10:.0f} points\n")

        # Final calculation
        print("📐 Calcul Final:")
        print(f"   TrustScore = ({doc['score']:.1f}×0.10 + {hist['score']:.1f}×0.40 + "
              f"{comp['score']:.1f}×0.30 + {fin['score']:.1f}×0.20) × 10")

        calculated = (doc['score'] * 0.10 + hist['score'] * 0.40 +
                      comp['score'] * 0.30 + fin['score'] * 0.20) * 10
        print(f"   TrustScore = {calculated:.0f} points")


def demo_badge_thresholds():
    """Show badge thresholds and requirements"""
    print_header("Seuils des Badges")

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  Badge         │  Score  │  Documents requis        │  Autres               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🥇 PLATINUM   │  ≥ 850  │  Tous (5/5)             │  Site visit*          ║
║  🥇 GOLD       │  ≥ 700  │  3 essentiels (RCM, CNI, NIF)  │  -           ║
║  🥈 SILVER     │  ≥ 550  │  2 documents            │  -                    ║
║  🥉 BRONZE     │  ≥ 400  │  1 document             │  -                    ║
║  ⚪ NONE       │  < 400  │  -                      │  -                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

*Site visit non implémenté pour le hackathon

📊 Mode COLD_START (< 3 mois d'historique):
   • Score maximum: 500 points
   • Badge maximum: BRONZE
   • Basé uniquement sur documents vérifiés

📊 Mode NORMAL (≥ 3 mois d'historique):
   • Score maximum: 1000 points
   • Badge maximum: PLATINUM
   • Algorithme complet 10/40/30/20
    """)


def main():
    """Run all demos"""
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*20 + "SmartKYC - TrustScore Calculator Demo" + " "*21 + "║")
    print("║" + " "*24 + "Le Badge de Confiance du B2B Africain" + " "*17 + "║")
    print("╚" + "═"*78 + "╝")

    # Run demos
    demo_merchant_profiles()
    demo_score_breakdown()
    demo_badge_thresholds()

    print_header("Fin de la Démonstration")
    print("\n✨ Pour plus d'informations, consultez TRUSTSCORE_USAGE.md")
    print("📝 Pour tester: python3 test_trustscore_calculator.py\n")


if __name__ == "__main__":
    main()
