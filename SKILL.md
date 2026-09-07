---
name: llm-wiki-engineering
description: ソフトウェアプロジェクトの要求・設計・検証結果・実践知と、それらを更新するTaskを保守するプロジェクト内LLM Wiki。
---

# LLM Wiki Engineering

作業方法を決める前に [README.md](README.md) と [TODO.md](TODO.md) をfresh-readする。標準起動は `Work 1 / Work 2 / Slot E` の2Slot+Eとし、直接の人間依頼はWork 1、Work 2はTaskとTODOを見直して独立に選ぶ。

個別Workを実行する場合は対象Task文書を読み、今回の範囲と完了・停止条件を確認する。各Workは自分の文章品質まで責任を持つ。

Slot Eでは [Wiki内部品質の独立点検](tasks/wiki-editorial-quality.md) を実行する。Work 1 / Work 2の成果物や中心主題を原則避け、現在の作業attentionから離れた既存Wiki Entryを再読して内部品質を保つ。

結果・適用条件・解釈・設計判断・再利用できる実践知は `wiki/` にまとめる。Run NoteにはWork 1 / Work 2 / Eそれぞれの実行証拠とRun-level contribution claimを残し、Wiki Entry-level claimと区別する。

Run Noteの `task` metadataはカンマ区切りで複数Taskを列挙でき、標準起動ではWork 1、Work 2、Slot Eの順に記す。例: `task: direct-request, DESIGN-MAINTENANCE, WIKI-EDITORIAL-QUALITY`。

起動の終了前にTODOを再読し、今回状態が変わった人間要望を更新する。Taskを一回実行したことだけでTODOを完了扱いにしない。

Taskの形成・2Slot+E・引継ぎ・claim運用は [Taskの運用](TASK_SYSTEM.md)、文章品質は [文章の品質基準](WRITING.md) を必要に応じて読む。
