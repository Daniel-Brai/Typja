import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from typja.analyzer import ValidationIssue
from typja.parser import CommentParser, FromImportStatement, ImportStatement, TypeAnnotation, TypjaComment


@dataclass
class LintRule:
    """
    Schema to represent a linting rule

    Attributes:
        name (str): Unique name of the linting rule
        message (str): Message template for the issue, can include placeholders for dynamic values
        severity (Literal["error", "warning"]): Severity level of the issue ('error' or 'warning')
        check (Callable[..., bool]): Function that checks if the rule is violated, should return True if valid and False if violated
        fixer (Callable[..., str] | None): Optional function that can provide an automatic fix for
    """

    name: str
    message: str
    severity: Literal["error", "warning"]
    check: Callable[..., bool]
    fixer: Callable[..., str] | None = None


class Linter:
    """
    Linter for typja in jinja templates
    """

    def __init__(self):
        self.rules = self._create_rules()
        self.comment_parser = CommentParser()

    def _create_rules(self) -> list[LintRule]:
        return [
            LintRule(
                name="prefer-pep604-union",
                message="Use PEP 604 union syntax (X | Y) instead of {old_style}",
                severity="warning",
                check=self._check_pep604_union,
                fixer=self._fix_pep604_union,
            ),
            LintRule(
                name="no-unused-imports",
                message="Import '{name}' is unused",
                severity="warning",
                check=self._check_unused_import,
                fixer=None,
            ),
            LintRule(
                name="no-duplicate-declarations",
                message="Duplicate declaration of '{name}'",
                severity="error",
                check=self._check_duplicate_declarations,
                fixer=None,
            ),
            LintRule(
                name="sorted-imports",
                message="Imports should be sorted alphabetically",
                severity="warning",
                check=self._check_sorted_imports,
                fixer=None,
            ),
            LintRule(
                name="no-redundant-none",
                message="Redundant None in union type",
                severity="warning",
                check=self._check_redundant_none,
                fixer=None,
            ),
        ]

    def lint_template(self, content: str, filename: str, config: dict[str, Any]) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []
        rule_config = config.get("linting", {})

        parsed_comments = None
        needs_comments = any(
            rule.name
            in [
                "no-unused-imports",
                "no-duplicate-declarations",
                "sorted-imports",
                "no-redundant-none",
            ]
            for rule in self.rules
        )

        if needs_comments:
            try:
                parsed_comments = self.comment_parser.parse_template(content, filename)
            except Exception:
                parsed_comments = []

        for rule in self.rules:
            if rule.name == "prefer-pep604-union":
                if not rule_config.get("prefer_pep604_unions", True):
                    continue
                severity = rule_config.get("union_style", "warning")
            elif rule.name == "no-unused-imports":
                if not rule_config.get("warn_unused_imports", True):
                    continue
                severity = rule.severity
            elif rule.name == "sorted-imports":
                if not rule_config.get("sort_imports", True):
                    continue
                severity = rule.severity
            else:
                severity = rule.severity

            rule_issues = self._apply_rule(rule, content, filename, severity, parsed_comments)
            issues.extend(rule_issues)

        return issues

    def _apply_rule(
        self,
        rule: LintRule,
        content: str,
        filename: str,
        severity: Literal["error", "warning"],
        parsed_comments: list[TypjaComment] | None,
    ) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []

        if rule.name == "prefer-pep604-union":
            for line_num, line in enumerate(content.splitlines(), 1):
                if "Optional[" in line or "Union[" in line:
                    old_style = self._extract_old_union(line)

                    if old_style:
                        new_style = self._fix_pep604_union(old_style)

                        issues.append(
                            ValidationIssue(
                                severity=severity,
                                message=rule.message.format(old_style=old_style),
                                filename=filename,
                                line=line_num,
                                hint=f"Use: {new_style}",
                            )
                        )

        elif rule.name == "no-unused-imports":
            if parsed_comments is not None:
                issues.extend(self._check_all_unused_imports(content, filename, severity, parsed_comments))

        elif rule.name == "no-duplicate-declarations":
            if parsed_comments is not None:
                issues.extend(self._check_all_duplicate_declarations(filename, severity, parsed_comments))

        elif rule.name == "sorted-imports":
            if parsed_comments is not None:
                issues.extend(self._check_all_sorted_imports(filename, severity, parsed_comments))

        elif rule.name == "no-redundant-none":
            if parsed_comments is not None:
                issues.extend(self._check_all_redundant_none(filename, severity, parsed_comments))

        return issues

    def _check_pep604_union(self, type_annotation: TypeAnnotation) -> bool:
        if type_annotation.name in ["Union", "Optional"]:
            if type_annotation.module == "typing":
                return False

        return True

    def _check_unused_import(self, import_name: str, content: str) -> bool:
        type_pattern = rf"\b{re.escape(import_name)}\b"

        if re.search(type_pattern, content):
            lines = content.splitlines()
            for line in lines:
                if "typja:import" in line or "typja:from" in line:
                    continue
                if re.search(type_pattern, line):
                    return True

        return False

    def _check_duplicate_declarations(self, declarations: dict[str, list]) -> bool:
        for _, occurrences in declarations.items():
            if len(occurrences) > 1:
                return False
        return True

    def _check_sorted_imports(self, imports: list[str]) -> bool:
        if len(imports) <= 1:
            return True
        return imports == sorted(imports)

    def _check_redundant_none(self, type_str: str) -> bool:
        if "|" in type_str:
            parts = [p.strip() for p in type_str.split("|")]
            none_count = parts.count("None")

            if none_count > 1:
                return False

        return True

    def _check_all_unused_imports(
        self,
        content: str,
        filename: str,
        severity: Literal["error", "warning"],
        parsed_comments: list[TypjaComment],
    ) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []

        for comment in parsed_comments:
            for decl in comment.declarations:
                if isinstance(decl, ImportStatement):
                    module = decl.module
                    line = decl.line

                    if not re.search(rf"\b{re.escape(module)}\.\w+", content):
                        issues.append(
                            ValidationIssue(
                                severity=severity,
                                message=f"Import '{module}' is unused",
                                filename=filename,
                                line=line,
                                hint=f"Remove unused import or use types from '{module}'",
                            )
                        )

                elif isinstance(decl, FromImportStatement):
                    module = decl.module
                    names = decl.names
                    line = decl.line

                    for name, alias in names:
                        check_name = alias if alias else name

                        if not self._check_unused_import(check_name, content):
                            issues.append(
                                ValidationIssue(
                                    severity=severity,
                                    message=f"Import '{name}' from '{module}' is unused",
                                    filename=filename,
                                    line=line,
                                    hint=f"Remove unused import '{name}'",
                                )
                            )

        return issues

    def _check_all_duplicate_declarations(
        self,
        filename: str,
        severity: Literal["error", "warning"],
        parsed_comments: list[TypjaComment],
    ) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []
        declarations: dict[str, list[tuple[int, str]]] = {}

        for comment in parsed_comments:
            for decl in comment.declarations:
                if hasattr(decl, "name"):
                    name = decl.name  # type: ignore[attr-defined]
                    decl_type = type(decl).__name__
                    key = f"{decl_type}:{name}"

                    if key not in declarations:
                        declarations[key] = []

                    declarations[key].append((decl.line, name))

        for key, occurrences in declarations.items():
            if len(occurrences) > 1:
                decl_type, name = key.split(":", 1)

                for line, _ in occurrences[1:]:
                    issues.append(
                        ValidationIssue(
                            severity=severity,
                            message=f"Duplicate declaration of '{name}'",
                            filename=filename,
                            line=line,
                            hint=f"'{name}' was already declared at line {occurrences[0][0]}",
                        )
                    )

        return issues

    def _check_all_sorted_imports(
        self,
        filename: str,
        severity: Literal["error", "warning"],
        parsed_comments: list[TypjaComment],
    ) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []
        imports_block: list[tuple[int, str, str]] = []
        last_import_line = -1

        for comment in parsed_comments:
            for decl in comment.declarations:
                if isinstance(decl, ImportStatement):
                    line = decl.line
                    module = decl.module
                    sort_key = f"0:{module}"
                    import_body = f"import {module}"

                    if last_import_line != -1 and line - last_import_line > 2:
                        if imports_block:
                            issues.extend(self._check_import_block_sorted(imports_block, filename, severity))
                            imports_block = []

                    imports_block.append((line, sort_key, import_body))
                    last_import_line = line

                elif isinstance(decl, FromImportStatement):
                    line = decl.line
                    module = decl.module
                    sort_key = f"1:{module}"
                    names_str = ", ".join(f"{name} as {alias}" if alias else name for name, alias in decl.names)
                    import_body = f"from {module} import {names_str}"

                    if last_import_line != -1 and line - last_import_line > 2:
                        if imports_block:
                            issues.extend(self._check_import_block_sorted(imports_block, filename, severity))
                            imports_block = []

                    imports_block.append((line, sort_key, import_body))
                    last_import_line = line

        if imports_block:
            issues.extend(self._check_import_block_sorted(imports_block, filename, severity))

        return issues

    def _check_import_block_sorted(
        self,
        imports_block: list[tuple[int, str, str]],
        filename: str,
        severity: Literal["error", "warning"],
    ) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []

        if len(imports_block) <= 1:
            return issues

        sorted_block = sorted(imports_block, key=lambda x: x[1])

        if imports_block != sorted_block:
            first_line = imports_block[0][0]
            issues.append(
                ValidationIssue(
                    severity=severity,
                    message="Imports should be sorted alphabetically",
                    filename=filename,
                    line=first_line,
                    hint="Group imports by type (import first, then from) and sort alphabetically",
                )
            )

        return issues

    def _check_all_redundant_none(
        self,
        filename: str,
        severity: Literal["error", "warning"],
        parsed_comments: list[TypjaComment],
    ) -> list[ValidationIssue]:

        issues: list[ValidationIssue] = []

        for comment in parsed_comments:
            for decl in comment.declarations:
                type_annotation = None
                line = decl.line

                if hasattr(decl, "type_annotation"):
                    type_annotation = decl.type_annotation  # type: ignore[attr-defined]

                if hasattr(decl, "params"):
                    params = decl.params  # type: ignore[attr-defined]
                    for _, param_type, _, _ in params:
                        if self._has_redundant_none(param_type):
                            issues.append(
                                ValidationIssue(
                                    severity=severity,
                                    message="Redundant None in union type",
                                    filename=filename,
                                    line=line,
                                    hint="Remove duplicate None types",
                                )
                            )

                if hasattr(decl, "return_type"):
                    return_type = decl.return_type  # type: ignore[attr-defined]
                    if self._has_redundant_none(return_type):
                        issues.append(
                            ValidationIssue(
                                severity=severity,
                                message="Redundant None in union type",
                                filename=filename,
                                line=line,
                                hint="Remove duplicate None types",
                            )
                        )

                if type_annotation and self._has_redundant_none(type_annotation):
                    issues.append(
                        ValidationIssue(
                            severity=severity,
                            message="Redundant None in union type",
                            filename=filename,
                            line=line,
                            hint="Remove duplicate None types",
                        )
                    )

        return issues

    def _has_redundant_none(self, type_annotation: TypeAnnotation) -> bool:
        if type_annotation.is_union and type_annotation.union_types:
            none_count = sum(1 for t in type_annotation.union_types if t.name == "None")
            return none_count > 1

        return False

    def _fix_pep604_union(self, old_union: str) -> str:
        if old_union.startswith("Optional["):
            inner = old_union[9:-1]
            return f"{inner} | None"

        if old_union.startswith("Union["):
            inner = old_union[6:-1]
            types = [t.strip() for t in self._split_union_args(inner)]
            return " | ".join(types)

        return old_union

    def _extract_old_union(self, line: str) -> str | None:
        import re

        match = re.search(r"Optional\[[^\]]+\]", line)
        if match:
            return match.group(0)

        match = re.search(r"Union\[[^\]]+\]", line)
        if match:
            return match.group(0)

        return None

    def _split_union_args(self, args: str) -> list[str]:
        result = []
        current = []
        depth = 0

        for char in args:
            if char in "[({":
                depth += 1
                current.append(char)
            elif char in "])}":
                depth -= 1
                current.append(char)
            elif char == "," and depth == 0:
                result.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            result.append("".join(current).strip())

        return result

    def auto_fix(self, content: str, issues: list[ValidationIssue]) -> str:
        fixed_content = content

        for issue in issues:
            if "Use PEP 604" in issue.message and issue.hint:
                if issue.hint.startswith("Use: "):
                    new_style = issue.hint[5:]
                    lines = fixed_content.splitlines()

                    if 0 < issue.line <= len(lines):
                        line = lines[issue.line - 1]
                        old_style = self._extract_old_union(line)

                        if old_style:
                            lines[issue.line - 1] = line.replace(old_style, new_style)
                            fixed_content = "\n".join(lines)

        return fixed_content
