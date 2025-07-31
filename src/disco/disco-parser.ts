import { JSDOM } from 'jsdom';
import * as fs from 'fs';
import * as path from 'path';

interface SkillNode {
    [skillName: string]: SkillNode | { termId?: string; children?: SkillNode };
}

interface SkillNodeWithMeta {
    termId?: string;
    children: SkillNode;
}

class DiscoSkillsParser {
    private dom: JSDOM;

    constructor(htmlContent: string) {
        this.dom = new JSDOM(htmlContent);
    }

    /**
     * Парсит HTML документ и извлекает древовидную структуру навыков
     */
    public parseSkillsTree(): SkillNode {
        const document = this.dom.window.document;
        
        // Ищем корневой список навыков
        const rootList = document.querySelector('ul.rootList');
        if (!rootList) {
            throw new Error('Корневой список навыков не найден');
        }

        const rootSkillsTree: SkillNode = {};
        
        // Находим все корневые элементы li.liItem, которые являются прямыми детьми rootList
        const rootSkillElements = rootList.querySelectorAll(':scope > li.liItem');
        
        for (const rootElement of rootSkillElements) {
            const skillElement = rootElement.querySelector('span.itemToBeAdded');
            if (!skillElement) continue;

            const skillName = this.cleanSkillName(skillElement.textContent);
            const termId = rootElement.getAttribute('data-termid');
            
            // Ищем вложенный контейнер для этого корневого элемента
            let nestedSkills: SkillNode = {};
            const nextSibling = rootElement.nextElementSibling;
            
            if (nextSibling && nextSibling.classList.contains('noBulletsLi')) {
                const nestedUl = nextSibling.querySelector('ul.innerUl');
                if (nestedUl) {
                    nestedSkills = this.parseNestedSkills(nestedUl);
                }
            }
            
            // Сохраняем навык с метаданными
            if (termId) {
                rootSkillsTree[skillName] = {
                    termId: termId,
                    children: nestedSkills
                } as any;
            } else {
                rootSkillsTree[skillName] = nestedSkills;
            }
        }

        return rootSkillsTree;
    }

    /**
     * Рекурсивно парсит вложенные навыки
     */
    private parseNestedSkills(ulElement: Element): SkillNode {
        const skills: SkillNode = {};
        
        // Получаем все прямые дочерние li элементы
        const listItems = ulElement.querySelectorAll(':scope > li.liItem');
        
        for (const li of listItems) {
            const skillElement = li.querySelector('span.itemToBeAdded');
            if (!skillElement) continue;

            const skillName = this.cleanSkillName(skillElement.textContent);
            const termId = li.getAttribute('data-termid');
            
            // Ищем вложенный список для этого навыка
            const nestedContainer = li.nextElementSibling;
            let nestedSkills: SkillNode = {};
            
            if (nestedContainer && nestedContainer.classList.contains('noBulletsLi')) {
                const nestedUl = nestedContainer.querySelector('ul.innerUl');
                if (nestedUl) {
                    nestedSkills = this.parseNestedSkills(nestedUl);
                }
            }
            
            // Сохраняем навык с метаданными если есть termId
            if (termId) {
                skills[skillName] = {
                    termId: termId,
                    children: nestedSkills
                } as any;
            } else {
                skills[skillName] = nestedSkills;
            }
        }
        
        return skills;
    }

    /**
     * Очищает название навыка от лишних символов
     */
    private cleanSkillName(text: string | null): string {
        if (!text) return '';
        return text.trim().replace(/\s+/g, ' ');
    }

    /**
     * Сохраняет структуру навыков в JSON файл
     */
    public saveToFile(skillsTree: SkillNode, outputPath: string): void {
        const jsonContent = JSON.stringify(skillsTree, null, 2);
        fs.writeFileSync(outputPath, jsonContent, 'utf-8');
        console.log(`Структура навыков сохранена в: ${outputPath}`);
    }
}

/**
 * Основная функция для парсинга DISCO навыков
 */
export async function parseDiscoSkills(htmlFilePath: string, outputPath: string): Promise<void> {
    const htmlContent = fs.readFileSync(htmlFilePath, 'utf-8');
        
    // Создаем парсер
    const parser = new DiscoSkillsParser(htmlContent);
    
    // Парсим структуру навыков
    const skillsTree = parser.parseSkillsTree();
    
    // Сохраняем результат
    parser.saveToFile(skillsTree, outputPath);
    
    console.log('Парсинг завершен успешно!');
    console.log(`Найдено навыков верхнего уровня: ${Object.keys(skillsTree).length}`);
}

// Запуск парсера если файл вызван напрямую
if (require.main === module) {
    const htmlPath = path.join(__dirname, 'DISCO II Portal.html');
    const outputPath = path.join(__dirname, 'disco-skills-tree.json');
    
    parseDiscoSkills(htmlPath, outputPath)
        .then(() => console.log('Готово!'))
        .catch(console.error);
} 