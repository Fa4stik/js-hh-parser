import * as fs from 'fs';
import * as path from 'path';

interface SkillNode {
    [skillName: string]: SkillNode | SkillNodeWithMeta;
}

interface SkillNodeWithMeta {
    termId?: string;
    children: SkillNode;
}

class DiscoSkillsAnalyzer {
    private skillsTree: SkillNode;

    constructor(jsonFilePath: string) {
        const content = fs.readFileSync(jsonFilePath, 'utf-8');
        this.skillsTree = JSON.parse(content);
    }

    /**
     * Проверяет, является ли узел метаузлом с termId и children
     */
    private isMetaNode(node: any): node is SkillNodeWithMeta {
        return node && typeof node === 'object' && 'children' in node;
    }

    /**
     * Получает дочерние элементы узла
     */
    private getChildren(node: any): SkillNode {
        if (this.isMetaNode(node)) {
            return node.children;
        }
        return node as SkillNode;
    }

    /**
     * Подсчитывает общее количество навыков в дереве
     */
    public countTotalSkills(): number {
        return this.countSkillsRecursive(this.skillsTree);
    }

    /**
     * Рекурсивно подсчитывает навыки
     */
    private countSkillsRecursive(node: SkillNode): number {
        let count = 0;
        
        for (const [skillName, nodeValue] of Object.entries(node)) {
            count += 1; // текущий навык
            const children = this.getChildren(nodeValue);
            if (Object.keys(children).length > 0) {
                count += this.countSkillsRecursive(children);
            }
        }
        
        return count;
    }

    /**
     * Получает все навыки определенного уровня
     */
    public getSkillsByLevel(level: number): string[] {
        const skills: string[] = [];
        this.collectSkillsByLevel(this.skillsTree, level, 0, skills);
        return skills;
    }

    /**
     * Рекурсивно собирает навыки определенного уровня
     */
    private collectSkillsByLevel(node: SkillNode, targetLevel: number, currentLevel: number, result: string[]): void {
        if (currentLevel === targetLevel) {
            result.push(...Object.keys(node));
            return;
        }

        for (const nodeValue of Object.values(node)) {
            const children = this.getChildren(nodeValue);
            if (Object.keys(children).length > 0) {
                this.collectSkillsByLevel(children, targetLevel, currentLevel + 1, result);
            }
        }
    }

    /**
     * Находит навык по пути
     */
    public findSkillByPath(skillPath: string[]): SkillNode | null {
        let current = this.skillsTree;
        
        for (const pathPart of skillPath) {
            if (current[pathPart]) {
                current = this.getChildren(current[pathPart]);
            } else {
                return null;
            }
        }
        
        return current;
    }

    /**
     * Поиск навыков по ключевому слову
     */
    public searchSkills(keyword: string): string[] {
        const foundSkills: string[] = [];
        this.searchSkillsRecursive(this.skillsTree, keyword.toLowerCase(), foundSkills);
        return foundSkills;
    }

    /**
     * Рекурсивный поиск навыков
     */
    private searchSkillsRecursive(node: SkillNode, keyword: string, result: string[]): void {
        for (const [skillName, nodeValue] of Object.entries(node)) {
            if (skillName.toLowerCase().includes(keyword)) {
                result.push(skillName);
            }
            
            const children = this.getChildren(nodeValue);
            if (Object.keys(children).length > 0) {
                this.searchSkillsRecursive(children, keyword, result);
            }
        }
    }

    /**
     * Получает максимальную глубину дерева
     */
    public getMaxDepth(): number {
        return this.calculateDepth(this.skillsTree);
    }

    /**
     * Рекурсивно вычисляет глубину
     */
    private calculateDepth(node: SkillNode): number {
        if (Object.keys(node).length === 0) {
            return 0;
        }

        let maxDepth = 0;
        for (const nodeValue of Object.values(node)) {
            const children = this.getChildren(nodeValue);
            const depth = this.calculateDepth(children);
            maxDepth = Math.max(maxDepth, depth);
        }

        return maxDepth + 1;
    }

    /**
     * Выводит статистику по структуре навыков
     */
    public printStatistics(): void {
        console.log('=== Статистика структуры навыков DISCO ===');
        console.log(`Общее количество навыков: ${this.countTotalSkills()}`);
        console.log(`Количество конечных навыков: ${this.countLeafSkills()}`);
        console.log(`Количество групп навыков: ${this.countTotalSkills() - this.countLeafSkills()}`);
        console.log(`Максимальная глубина дерева: ${this.getMaxDepth()}`);
        
        console.log('\n=== Навыки по уровням ===');
        for (let level = 0; level < this.getMaxDepth(); level++) {
            const skillsAtLevel = this.getSkillsByLevel(level);
            console.log(`Уровень ${level}: ${skillsAtLevel.length} навыков`);
            if (level === 0) {
                console.log(`  Примеры: ${skillsAtLevel.slice(0, 3).join(', ')}`);
            }
        }
    }

    /**
     * Экспортирует плоский список всех навыков
     */
    public exportFlatSkillsList(outputPath: string): void {
        const allSkills: string[] = [];
        this.collectAllSkills(this.skillsTree, allSkills);
        
        const content = allSkills.map(skill => `${skill}`).join('\n');
        fs.writeFileSync(outputPath, content, 'utf-8');
        
        console.log(`Плоский список навыков сохранен в: ${outputPath}`);
        console.log(`Всего навыков: ${allSkills.length}`);
    }

    /**
     * Рекурсивно собирает все навыки в плоский список
     */
    private collectAllSkills(node: SkillNode, result: string[]): void {
        for (const [skillName, nodeValue] of Object.entries(node)) {
            result.push(skillName);
            const children = this.getChildren(nodeValue);
            if (Object.keys(children).length > 0) {
                this.collectAllSkills(children, result);
            }
        }
    }

    /**
     * Получает только конечные навыки (листья дерева) без групп
     */
    public getLeafSkills(): string[] {
        const leafSkills: string[] = [];
        this.collectLeafSkills(this.skillsTree, leafSkills);
        return leafSkills;
    }

    /**
     * Рекурсивно собирает только конечные навыки (листья дерева)
     */
    private collectLeafSkills(node: SkillNode, result: string[]): void {
        for (const [skillName, nodeValue] of Object.entries(node)) {
            const children = this.getChildren(nodeValue);
            // Если у навыка нет вложенных навыков, это конечный навык
            if (Object.keys(children).length === 0) {
                result.push(skillName);
            } else {
                // Рекурсивно проверяем вложенные навыки
                this.collectLeafSkills(children, result);
            }
        }
    }

    /**
     * Экспортирует только конечные навыки в JSON формате {"Название навыка": {}}
     */
    public exportLeafSkillsAsJson(outputPath: string): void {
        const leafSkills = this.getLeafSkills();
        const leafSkillsJson: SkillNode = {};
        
        // Создаем объект с конечными навыками
        leafSkills.forEach(skill => {
            leafSkillsJson[skill] = {};
        });
        
        fs.writeFileSync(outputPath, JSON.stringify(leafSkillsJson, null, 2), 'utf-8');
        
        console.log(`Конечные навыки сохранены в: ${outputPath}`);
        console.log(`Всего конечных навыков: ${leafSkills.length}`);
    }

    /**
     * Подсчитывает количество конечных навыков
     */
    public countLeafSkills(): number {
        return this.getLeafSkills().length;
    }
}

// Функция для демонстрации работы с навыками
export function analyzeDiscoSkills(): void {
    const jsonPath = path.join(__dirname, 'disco-skills-tree.json');
    const analyzer = new DiscoSkillsAnalyzer(jsonPath);
    
    // Выводим статистику
    analyzer.printStatistics();
    
    // Поиск компьютерных навыков
    console.log('\n=== Поиск компьютерных навыков ===');
    const computerSkills = analyzer.searchSkills('программ');
    console.log(`Найдено навыков, содержащих "программ": ${computerSkills.length}`);
    console.log('Первые 10:', computerSkills.slice(0, 10));
    
    // Экспорт плоского списка
    const outputPath = path.join(__dirname, 'disco-skills-flat-list.txt');
    analyzer.exportFlatSkillsList(outputPath);
    
    // Экспорт только конечных навыков
    console.log('\n=== Экспорт конечных навыков ===');
    const leafSkillsPath = path.join(__dirname, '..', 'disco-leaf-skills.json');
    analyzer.exportLeafSkillsAsJson(leafSkillsPath);
    
    // Показываем примеры конечных навыков
    const leafSkills = analyzer.getLeafSkills();
    console.log('\nПримеры конечных навыков:');
    leafSkills.slice(0, 10).forEach((skill, index) => {
        console.log(`${skill}`);
    });
}

// Функция для экспорта только конечных навыков
export function exportLeafSkills(outputPath?: string): string[] {
    const jsonPath = path.join(__dirname, 'disco-skills-tree.json');
    const analyzer = new DiscoSkillsAnalyzer(jsonPath);
    
    const leafSkills = analyzer.getLeafSkills();
    const leafSkillsJson: SkillNode = {};
    
    // Создаем объект с конечными навыками
    leafSkills.forEach(skill => {
        leafSkillsJson[skill] = {};
    });
    
    // Сохраняем в файл если указан путь
    if (outputPath) {
        fs.writeFileSync(outputPath, Object.keys(leafSkillsJson).join('\n'), 'utf-8');
        console.log(`Конечные навыки сохранены в: ${outputPath}`);
        console.log(`Всего конечных навыков: ${leafSkills.length}`);
    }
    
    return Object.keys(leafSkillsJson);
}

// Запуск анализа если файл вызван напрямую
if (require.main === module) {
    analyzeDiscoSkills();
} 