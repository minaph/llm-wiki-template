# Task一覧

Taskは、これから行う作業の目的・根拠・行為・完了条件を定める文書である。初期版は手動で選択する。メタデータの意味、Taskの形成、2Slot+Eの選択方法は [Taskの運用](../TASK_SYSTEM.md) を参照する。

人間の明示的要求はまず [TODO](../TODO.md) で現在状態を追跡する。TODO項目を自動的にTaskへ変換せず、既存Taskの一部、単発Task、集中Task、条件付きTask、常設Task、直接作業、Task化しない判断から適切な形成先を選ぶ。

標準Taskは次の7件である。最初の6件はWork 1 / Work 2の候補、7件目はSlot E専用の独立品質管理Taskである。IDは参照用に維持し、題名と本文は作業内容が分かる表現にする。

1. [設計文書の保守](design-maintenance.md) — コード・要求・検証結果の変更に合わせて設計文書を更新する。
2. [コードと履歴からの設計調査](code-design-rediscovery.md) — 現行コードとGit履歴から暗黙の設計を調べる。
3. [要求と設計・実装の整合点検](client-needs-alignment.md) — 要求と設計・実装・検証の対応を確認する。
4. [未検証事項と検証の有効性の点検](verification-debt-review.md) — 未検証の主張や、テスト・環境の変化で無効になった検証を見つける。
5. [設計案の比較・検討](design-option-exploration.md) — 重要な設計判断の代替案と、判断に必要な検証を検討する。
6. [Task運用の点検](task-system-health.md) — 2Slotの偏り、TODOや引継ぎの滞留、結果の未還流など具体的な問題が繰り返された場合に実施する。
7. [Wiki内部品質の独立点検](wiki-editorial-quality.md) — Work 1 / Work 2の主題から離れた既存Wiki Entryを再読し、文章・claim・根拠接続・構造の品質を保つ。標準起動ではSlot Eに固定する。

標準起動ではWork 1とWork 2を別々に選ぶ。直接の人間依頼はWork 1に置き、Work 2はTask一覧とTODOをもう一度見て、別の問い・根拠面・判断差を持つ作業を選ぶ。同じTaskを二枠に選ぶ場合も、単なる再包装になっていないことを確認する。

文章を変更したTaskは、そのWork内で読み直しまで行う。Slot Eはその成果物を再校正するのではなく、`WIKI-EDITORIAL-QUALITY` を実行してWork 1 / Work 2から十分に離れた既存Wiki Entryを独立に点検する。これにより今回の作業対象に限らずWiki内部品質を継続保守する。

検証を実行する場合も [Taskテンプレート](_TEMPLATE.md) を使い、`type: verification` とする。単発・常設などの存続形態と終了・停止・再開条件は本文に書く。検証結果と設計判断はWiki、実行ログ・作業過程・Run-level contribution claimはRun Noteに記録する。
