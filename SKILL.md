---
name: llm-wiki-engineering
description: ソフトウェアプロジェクトの要求・設計・検証結果・実践知と、それらを更新するTaskを保守するプロジェクト内LLM Wiki。
---

# LLM Wiki Engineering

作業方法を決める前に [README.md](README.md) と [TODO.md](TODO.md) をfresh-readする。標準起動は `Work 1 / Work 2 / Slot E` の2Slot+Eとし、直接の人間依頼はWork 1、Work 2はTaskとTODOを見直して独立に選ぶ。

個別Workを実行する場合は対象Task文書を読み、今回の範囲と完了・停止条件を確認する。各Workは自分の文章品質まで責任を持ち、Slot Eでは今回の主要成果を独立に再読する。

結果・適用条件・解釈・設計判断・再利用できる実践知は `wiki/` にまとめる。Run NoteにはWorkごとの実行証拠とRun-level contribution claimを残し、Wiki Entry-level claimと区別する。

起動の終了前にTODOを再読し、今回状態が変わった人間要望を更新する。Taskを一回実行したことだけでTODOを完了扱いにしない。

Taskの形成・2Slot+E・引継ぎ・claim運用は [Taskの運用](TASK_SYSTEM.md)、文章品質は [文章の品質基準](WRITING.md) を必要に応じて読む。
