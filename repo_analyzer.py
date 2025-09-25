"""
🔍 SageVault Repository Type Detection
Intelligent analysis of file trees to detect project types and generate tailored quickstart guides.
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class ProjectType:
    """Detected project type with metadata"""
    name: str
    confidence: float
    indicators: List[str]  # File patterns that led to detection
    version: Optional[str] = None
    framework: Optional[str] = None

@dataclass
class QuickstartGuide:
    """Generated quickstart guide for a project type"""
    title: str
    description: str
    prerequisites: List[str]
    install_commands: List[str]
    run_commands: List[str]
    additional_notes: List[str]
    links: List[Dict[str, str]]  # {"text": "...", "url": "..."}

class RepositoryAnalyzer:
    """
    Analyzes repository file trees to detect project types and generate
    appropriate quickstart guides without code execution.
    """
    
    # File patterns for different project types
    DETECTION_PATTERNS = {
        'python': {
            'strong': ['requirements.txt', 'pyproject.toml', 'setup.py', 'setup.cfg', 'Pipfile'],
            'medium': ['environment.yml', 'conda.yml', 'poetry.lock'],
            'weak': ['*.py', '__pycache__/', '.python-version'],
            'frameworks': {
                'django': ['manage.py', 'settings.py', 'django', 'Django'],
                'flask': ['app.py', 'flask', 'Flask'],
                'fastapi': ['fastapi', 'FastAPI', 'uvicorn'],
                'streamlit': ['streamlit', 'Streamlit', '.streamlit/'],
                'jupyter': ['*.ipynb', '.ipynb_checkpoints/', 'jupyter'],
                'pytest': ['pytest.ini', 'conftest.py', 'test_*.py'],
                'celery': ['celery', 'Celery', 'celeryconfig.py']
            }
        },
        'nodejs': {
            'strong': ['package.json', 'package-lock.json', 'yarn.lock'],
            'medium': ['node_modules/', '.nvmrc', '.node-version'],
            'weak': ['*.js', '*.ts', '*.json'],
            'frameworks': {
                'react': ['react', 'React', 'jsx', 'create-react-app'],
                'vue': ['vue', 'Vue', 'vue.config.js'],
                'angular': ['angular', 'Angular', '@angular/', 'angular.json'],
                'express': ['express', 'Express'],
                'next': ['next', 'Next.js', 'next.config.js'],
                'nuxt': ['nuxt', 'Nuxt', 'nuxt.config.js'],
                'svelte': ['svelte', 'Svelte', 'svelte.config.js'],
                'electron': ['electron', 'Electron']
            }
        },
        'docker': {
            'strong': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
            'medium': ['.dockerignore', 'docker-compose.*.yml'],
            'weak': ['*.dockerfile', 'Dockerfile.*'],
            'frameworks': {
                'k8s': ['*.yaml', '*.yml', 'kustomization.yaml', 'deployment.yaml'],
                'helm': ['Chart.yaml', 'values.yaml', 'templates/']
            }
        },
        'rust': {
            'strong': ['Cargo.toml', 'Cargo.lock'],
            'medium': ['src/main.rs', 'src/lib.rs'],
            'weak': ['*.rs', 'target/'],
            'frameworks': {
                'actix': ['actix', 'actix-web'],
                'rocket': ['rocket', 'Rocket'],
                'warp': ['warp'],
                'tokio': ['tokio']
            }
        },
        'go': {
            'strong': ['go.mod', 'go.sum'],
            'medium': ['main.go', 'Gopkg.toml'],
            'weak': ['*.go', 'vendor/'],
            'frameworks': {
                'gin': ['gin', 'gin-gonic'],
                'echo': ['echo', 'labstack/echo'],
                'fiber': ['fiber', 'gofiber'],
                'gorilla': ['gorilla', 'gorilla/mux']
            }
        },
        'java': {
            'strong': ['pom.xml', 'build.gradle', 'gradlew'],
            'medium': ['src/main/java/', 'build.xml'],
            'weak': ['*.java', '*.jar', 'target/', 'build/'],
            'frameworks': {
                'spring': ['spring', 'Spring', '@SpringBootApplication'],
                'android': ['AndroidManifest.xml', 'app/build.gradle'],
                'maven': ['pom.xml', '.m2/'],
                'gradle': ['build.gradle', 'gradlew', 'gradle/']
            }
        },
        'dotnet': {
            'strong': ['*.csproj', '*.sln', 'project.json'],
            'medium': ['*.cs', 'packages.config', 'nuget.config'],
            'weak': ['bin/', 'obj/', '*.dll'],
            'frameworks': {
                'aspnet': ['asp.net', 'ASP.NET', 'Startup.cs'],
                'blazor': ['blazor', 'Blazor', '*.razor'],
                'xamarin': ['xamarin', 'Xamarin'],
                'unity': ['unity', 'Unity', 'Assets/', 'ProjectSettings/']
            }
        },
        'ruby': {
            'strong': ['Gemfile', 'Gemfile.lock', 'Rakefile'],
            'medium': ['*.gemspec', 'config.ru'],
            'weak': ['*.rb', 'lib/', 'spec/'],
            'frameworks': {
                'rails': ['rails', 'Rails', 'config/application.rb'],
                'sinatra': ['sinatra', 'Sinatra'],
                'jekyll': ['jekyll', '_config.yml', '_posts/']
            }
        },
        'php': {
            'strong': ['composer.json', 'composer.lock'],
            'medium': ['index.php', 'autoload.php'],
            'weak': ['*.php', 'vendor/'],
            'frameworks': {
                'laravel': ['laravel', 'Laravel', 'artisan'],
                'symfony': ['symfony', 'Symfony'],
                'wordpress': ['wp-config.php', 'wp-content/'],
                'drupal': ['drupal', 'Drupal', 'modules/', 'themes/']
            }
        }
    }
    
    def __init__(self):
        self.detected_types = []
        self.file_list = []
        self.content_samples = {}
    
    def analyze_repository(self, file_list: List[str], content_samples: Dict[str, str] = None) -> List[ProjectType]:
        """
        Analyze repository files to detect project types
        
        Args:
            file_list: List of file paths in the repository
            content_samples: Optional dict of filename -> content for deeper analysis
        
        Returns:
            List of detected project types with confidence scores
        """
        self.file_list = file_list
        self.content_samples = content_samples or {}
        self.detected_types = []
        
        # Normalize file paths
        normalized_files = [f.replace('\\', '/').lower() for f in file_list]
        
        # Detect each project type
        for project_type, patterns in self.DETECTION_PATTERNS.items():
            confidence, indicators, framework, version = self._calculate_confidence(
                project_type, patterns, normalized_files
            )
            
            if confidence > 0.1:  # Minimum threshold
                self.detected_types.append(ProjectType(
                    name=project_type,
                    confidence=confidence,
                    indicators=indicators,
                    framework=framework,
                    version=version
                ))
        
        # Sort by confidence
        self.detected_types.sort(key=lambda x: x.confidence, reverse=True)
        return self.detected_types
    
    def _calculate_confidence(self, project_type: str, patterns: Dict, files: List[str]) -> Tuple[float, List[str], Optional[str], Optional[str]]:
        """Calculate confidence score for a project type"""
        confidence = 0.0
        indicators = []
        detected_framework = None
        detected_version = None
        
        # Check strong indicators (high confidence)
        for pattern in patterns['strong']:
            matches = self._find_pattern_matches(pattern, files)
            if matches:
                confidence += 0.4
                indicators.extend(matches)
        
        # Check medium indicators
        for pattern in patterns['medium']:
            matches = self._find_pattern_matches(pattern, files)
            if matches:
                confidence += 0.2
                indicators.extend(matches)
        
        # Check weak indicators
        weak_matches = 0
        for pattern in patterns['weak']:
            matches = self._find_pattern_matches(pattern, files)
            if matches:
                weak_matches += len(matches)
                indicators.extend(matches[:2])  # Limit to avoid spam
        
        # Weak indicators contribute less, with diminishing returns
        confidence += min(weak_matches * 0.05, 0.3)
        
        # Check for specific frameworks
        if 'frameworks' in patterns:
            framework_confidence = 0.0
            for framework, fw_patterns in patterns['frameworks'].items():
                fw_matches = sum(1 for pattern in fw_patterns 
                                if self._find_pattern_matches(pattern, files))
                if fw_matches > 0:
                    if fw_matches > framework_confidence:
                        framework_confidence = fw_matches
                        detected_framework = framework
                        confidence += 0.1  # Bonus for framework detection
        
        # Try to extract version information
        detected_version = self._extract_version_info(project_type, indicators)
        
        return min(confidence, 1.0), list(set(indicators)), detected_framework, detected_version
    
    def _find_pattern_matches(self, pattern: str, files: List[str]) -> List[str]:
        """Find files matching a pattern"""
        matches = []
        
        if pattern.endswith('/'):
            # Directory pattern
            dir_pattern = pattern.rstrip('/')
            matches = [f for f in files if f.startswith(dir_pattern + '/') or f == dir_pattern]
        elif '*' in pattern:
            # Wildcard pattern
            import fnmatch
            matches = [f for f in files if fnmatch.fnmatch(f, pattern)]
        else:
            # Exact match or substring
            matches = [f for f in files if pattern in f]
        
        return matches[:5]  # Limit results
    
    def _extract_version_info(self, project_type: str, indicators: List[str]) -> Optional[str]:
        """Extract version information from file contents"""
        if not self.content_samples:
            return None
        
        version_patterns = {
            'python': [
                r'python_requires\s*=\s*["\']([^"\']+)["\']',
                r'Programming Language :: Python :: ([0-9.]+)',
                r'version\s*=\s*["\']([^"\']+)["\']'
            ],
            'nodejs': [
                r'"version"\s*:\s*"([^"]+)"',
                r'"node"\s*:\s*"([^"]+)"'
            ],
            'java': [
                r'<java\.version>([^<]+)</java\.version>',
                r'<maven\.compiler\.source>([^<]+)</maven\.compiler\.source>'
            ]
        }
        
        if project_type in version_patterns:
            for indicator in indicators:
                if indicator in self.content_samples:
                    content = self.content_samples[indicator]
                    for pattern in version_patterns[project_type]:
                        match = re.search(pattern, content)
                        if match:
                            return match.group(1)
        
        return None
    
    def generate_quickstart_guide(self, project_type: ProjectType) -> QuickstartGuide:
        """Generate a quickstart guide for the detected project type"""
        
        # Define quickstart templates
        templates = {
            'python': self._python_quickstart,
            'nodejs': self._nodejs_quickstart,
            'docker': self._docker_quickstart,
            'rust': self._rust_quickstart,
            'go': self._go_quickstart,
            'java': self._java_quickstart,
            'ruby': self._ruby_quickstart,
            'php': self._php_quickstart,
            'dotnet': self._dotnet_quickstart
        }
        
        if project_type.name in templates:
            return templates[project_type.name](project_type)
        else:
            return self._generic_quickstart(project_type)
    
    def _python_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        """Generate Python project quickstart"""
        framework = project_type.framework
        
        # Base Python setup
        install_commands = []
        run_commands = []
        prerequisites = ["Python 3.7+"]
        
        # Check for different Python dependency managers
        if 'requirements.txt' in project_type.indicators:
            install_commands.append("pip install -r requirements.txt")
        elif 'pyproject.toml' in project_type.indicators:
            install_commands.append("pip install -e .")
            prerequisites.append("pip (or pipenv/poetry)")
        elif 'Pipfile' in project_type.indicators:
            install_commands.append("pipenv install")
            run_commands.append("pipenv shell")
            prerequisites.append("pipenv")
        elif 'environment.yml' in project_type.indicators:
            install_commands.append("conda env create -f environment.yml")
            run_commands.append("conda activate <env-name>")
            prerequisites = ["Anaconda/Miniconda"]
        
        # Framework-specific commands
        if framework == 'django':
            run_commands.extend([
                "python manage.py migrate",
                "python manage.py runserver"
            ])
        elif framework == 'flask':
            run_commands.append("python app.py")
        elif framework == 'fastapi':
            run_commands.append("uvicorn main:app --reload")
        elif framework == 'streamlit':
            run_commands.append("streamlit run app.py")
        elif framework == 'jupyter':
            run_commands.append("jupyter notebook")
        else:
            # Generic Python
            if 'main.py' in str(self.file_list):
                run_commands.append("python main.py")
            elif 'app.py' in str(self.file_list):
                run_commands.append("python app.py")
            else:
                run_commands.append("python <script>.py")
        
        title = f"Python{f' ({framework.title()})' if framework else ''} Project"
        description = f"This appears to be a Python project{f' using {framework}' if framework else ''}."
        
        return QuickstartGuide(
            title=title,
            description=description,
            prerequisites=prerequisites,
            install_commands=install_commands,
            run_commands=run_commands,
            additional_notes=[
                "Consider using a virtual environment: `python -m venv venv`",
                "Activate with: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)"
            ],
            links=[
                {"text": "Python Documentation", "url": "https://docs.python.org/"},
                {"text": "Virtual Environments Guide", "url": "https://docs.python.org/3/tutorial/venv.html"}
            ]
        )
    
    def _nodejs_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        """Generate Node.js project quickstart"""
        framework = project_type.framework
        
        install_commands = []
        run_commands = []
        
        # Package manager detection
        if 'yarn.lock' in project_type.indicators:
            install_commands.append("yarn install")
            run_commands.append("yarn start")
        else:
            install_commands.append("npm install")
            run_commands.append("npm start")
        
        # Framework-specific commands
        additional_commands = []
        if framework == 'react':
            additional_commands.extend(["npm run build", "npm test"])
        elif framework == 'next':
            additional_commands.extend(["npm run build", "npm run dev"])
        elif framework == 'vue':
            additional_commands.extend(["npm run serve", "npm run build"])
        elif framework == 'angular':
            run_commands = ["ng serve"]
            additional_commands.extend(["ng build", "ng test"])
        
        title = f"Node.js{f' ({framework.title()})' if framework else ''} Project"
        description = f"This appears to be a Node.js project{f' using {framework}' if framework else ''}."
        
        return QuickstartGuide(
            title=title,
            description=description,
            prerequisites=["Node.js 14+", "npm or yarn"],
            install_commands=install_commands,
            run_commands=run_commands + additional_commands,
            additional_notes=[
                "Check package.json for available scripts",
                "Use `npm run <script>` to run custom scripts"
            ],
            links=[
                {"text": "Node.js Documentation", "url": "https://nodejs.org/docs/"},
                {"text": "npm Documentation", "url": "https://docs.npmjs.com/"}
            ]
        )
    
    def _docker_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        """Generate Docker project quickstart"""
        install_commands = []
        run_commands = []
        
        if 'docker-compose.yml' in project_type.indicators or 'docker-compose.yaml' in project_type.indicators:
            run_commands.extend([
                "docker-compose up -d",
                "docker-compose logs -f"
            ])
            install_commands.append("# No installation needed - using Docker Compose")
        elif 'Dockerfile' in project_type.indicators:
            run_commands.extend([
                "docker build -t app-name .",
                "docker run -p 8080:8080 app-name"
            ])
            install_commands.append("# Build the Docker image first")
        
        return QuickstartGuide(
            title="Containerized Application",
            description="This project uses Docker for containerization.",
            prerequisites=["Docker", "Docker Compose (if using compose files)"],
            install_commands=install_commands,
            run_commands=run_commands,
            additional_notes=[
                "Adjust port mappings as needed",
                "Check Dockerfile and docker-compose.yml for specific configuration",
                "Use `docker-compose down` to stop services"
            ],
            links=[
                {"text": "Docker Documentation", "url": "https://docs.docker.com/"},
                {"text": "Docker Compose Guide", "url": "https://docs.docker.com/compose/"}
            ]
        )
    
    def _generic_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        """Generate generic quickstart for unknown project types"""
        return QuickstartGuide(
            title=f"{project_type.name.title()} Project",
            description=f"This appears to be a {project_type.name} project.",
            prerequisites=[f"{project_type.name.title()} runtime/compiler"],
            install_commands=["# Install dependencies according to project documentation"],
            run_commands=["# Run according to project documentation"],
            additional_notes=[
                "Check README.md for specific instructions",
                "Look for setup scripts or configuration files"
            ],
            links=[
                {"text": "Project Documentation", "url": "#"}
            ]
        )
    
    # Additional language quickstart methods would follow similar patterns...
    def _rust_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        return QuickstartGuide(
            title="Rust Project",
            description="This is a Rust project using Cargo.",
            prerequisites=["Rust", "Cargo"],
            install_commands=["cargo build"],
            run_commands=["cargo run"],
            additional_notes=["Use `cargo test` to run tests", "Use `cargo doc --open` for documentation"],  
            links=[{"text": "Rust Documentation", "url": "https://doc.rust-lang.org/"}]
        )
    
    def _go_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        return QuickstartGuide(
            title="Go Project",
            description="This is a Go project.",
            prerequisites=["Go 1.16+"],
            install_commands=["go mod download"],
            run_commands=["go run main.go"],
            additional_notes=["Use `go build` to compile", "Use `go test ./...` to run tests"],
            links=[{"text": "Go Documentation", "url": "https://golang.org/doc/"}]
        )
    
    def _java_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        if 'pom.xml' in project_type.indicators:
            return QuickstartGuide(
                title="Java Maven Project",
                description="This is a Java project using Maven.",
                prerequisites=["Java 8+", "Maven"],
                install_commands=["mvn clean install"],
                run_commands=["mvn spring-boot:run" if project_type.framework == 'spring' else "mvn exec:java"],
                additional_notes=["Use `mvn test` to run tests", "Check pom.xml for project configuration"],
                links=[{"text": "Maven Documentation", "url": "https://maven.apache.org/guides/"}]
            )
        else:
            return QuickstartGuide(
                title="Java Gradle Project", 
                description="This is a Java project using Gradle.",
                prerequisites=["Java 8+", "Gradle"],
                install_commands=["./gradlew build"],
                run_commands=["./gradlew run"],
                additional_notes=["Use `./gradlew test` to run tests"],
                links=[{"text": "Gradle Documentation", "url": "https://docs.gradle.org/"}]
            )
    
    def _ruby_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        return QuickstartGuide(
            title=f"Ruby{f' ({project_type.framework.title()})' if project_type.framework else ''} Project",
            description=f"This is a Ruby project{f' using {project_type.framework}' if project_type.framework else ''}.",
            prerequisites=["Ruby", "Bundler"],
            install_commands=["bundle install"],
            run_commands=["ruby app.rb" if project_type.framework != 'rails' else "rails server"],
            additional_notes=["Use `bundle exec` to run commands in the correct environment"],
            links=[{"text": "Ruby Documentation", "url": "https://ruby-doc.org/"}]
        )
    
    def _php_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        return QuickstartGuide(
            title=f"PHP{f' ({project_type.framework.title()})' if project_type.framework else ''} Project",
            description=f"This is a PHP project{f' using {project_type.framework}' if project_type.framework else ''}.",
            prerequisites=["PHP 7.4+", "Composer"],
            install_commands=["composer install"],
            run_commands=["php -S localhost:8000"] if not project_type.framework else ["# Use framework-specific server"],
            additional_notes=["Configure web server (Apache/Nginx) for production"],
            links=[{"text": "PHP Documentation", "url": "https://www.php.net/docs.php"}]
        )
    
    def _dotnet_quickstart(self, project_type: ProjectType) -> QuickstartGuide:
        return QuickstartGuide(
            title=".NET Project",
            description="This is a .NET project.",
            prerequisites=[".NET SDK"],
            install_commands=["dotnet restore"],
            run_commands=["dotnet run"],
            additional_notes=["Use `dotnet build` to compile", "Use `dotnet test` to run tests"],
            links=[{"text": ".NET Documentation", "url": "https://docs.microsoft.com/dotnet/"}]
        )

# Global repository analyzer instance
repo_analyzer = RepositoryAnalyzer()

# Example usage:
"""
# Analyze repository
file_list = ["requirements.txt", "app.py", "streamlit_app.py", "README.md"]
detected_types = repo_analyzer.analyze_repository(file_list)

# Generate quickstart guide
if detected_types:
    primary_type = detected_types[0]  # Highest confidence
    guide = repo_analyzer.generate_quickstart_guide(primary_type)
    print(f"Project Type: {guide.title}")
    print(f"Install: {' && '.join(guide.install_commands)}")
    print(f"Run: {' && '.join(guide.run_commands)}")
"""