import { exportLeafSkills } from './disco-analyzer';
import * as path from 'path';

// Пример использования функции для получения только конечных навыков
async function demonstrateLeafSkills() {
    console.log('=== Демонстрация получения только конечных навыков ===\n');
    
    // 1. Получение конечных навыков без сохранения в файл
    console.log('1. Получение конечных навыков в память:');
    const leafSkills = exportLeafSkills();
    const skillNames = Object.keys(leafSkills);
    
    console.log(`Всего конечных навыков: ${skillNames.length}`);
    console.log('Первые 10 навыков:');
    skillNames.slice(0, 10).forEach((skill, index) => {
        console.log(`   ${index + 1}. ${skill}`);
    });
    
    // 2. Сохранение конечных навыков в файл
    console.log('\n2. Сохранение конечных навыков в файл:');
    const outputPath = path.join(__dirname, 'example-leaf-skills.txt');
    exportLeafSkills(outputPath);
    
    // 3. Пример поиска конкретных навыков
    console.log('\n3. Поиск конкретных навыков:');
    const programmingSkills = skillNames.filter(skill => 
        skill.toLowerCase().includes('программ') || 
        skill.toLowerCase().includes('java') ||
        skill.toLowerCase().includes('python') ||
        skill.toLowerCase().includes('javascript')
    );
    
    console.log(`Найдено программистских навыков: ${programmingSkills.length}`);
    programmingSkills.forEach((skill, index) => {
        console.log(`   ${index + 1}. ${skill}`);
    });
    
    // 4. Пример фильтрации по категориям
    console.log('\n4. Навыки по категориям:');
    const categories = {
        'Водительские права': skillNames.filter(skill => skill.includes('водительские права')),
        'Языки программирования': skillNames.filter(skill => 
            skill.toLowerCase().includes('java') || 
            skill.toLowerCase().includes('python') ||
            skill.toLowerCase().includes('javascript') ||
            skill.toLowerCase().includes('php')
        ),
        'Базы данных': skillNames.filter(skill => 
            skill.toLowerCase().includes('sql') ||
            skill.toLowerCase().includes('mysql') ||
            skill.toLowerCase().includes('postgresql') ||
            skill.toLowerCase().includes('oracle')
        ),
        'Операционные системы': skillNames.filter(skill => 
            skill.toLowerCase().includes('windows') ||
            skill.toLowerCase().includes('linux') ||
            skill.toLowerCase().includes('unix')
        )
    };
    
    Object.entries(categories).forEach(([category, skills]) => {
        console.log(`${category}: ${skills.length} навыков`);
        if (skills.length > 0) {
            console.log(`   Примеры: ${skills.slice(0, 3).join(', ')}`);
        }
    });
}

// Запуск демонстрации
demonstrateLeafSkills().catch(console.error); 