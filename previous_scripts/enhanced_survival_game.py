import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 150, 255)
GREEN = (100, 200, 100)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
RED = (255, 100, 100)
YELLOW = (255, 255, 100)
DARK_BLUE = (50, 100, 200)
LIGHT_BLUE = (200, 220, 255)
SKIN_COLOR = (255, 220, 177)

# Game settings
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
INITIAL_STEP_SPEED = 0.8
MAX_STEP_SPEED = 4
STEP_SPAWN_RATE = 120
GRAB_DISTANCE = 50  # Increased grab distance
EASY_STEP_PROBABILITY_START = 0.9  # 90% easy steps at start
EASY_STEP_PROBABILITY_END = 0.5    # 50% easy steps at high difficulty

class Plane:
    def __init__(self):
        self.x = -150
        self.y = 80
        self.width = 100
        self.height = 40
        self.speed = 2.5
        self.active = False
        self.player_jumped = False
        
    def update(self):
        if self.active and not self.player_jumped:
            self.x += self.speed
            
    def should_player_jump(self):
        return self.x > SCREEN_WIDTH // 2 - 50
        
    def draw(self, screen):
        if self.active:
            # Plane body
            pygame.draw.ellipse(screen, GRAY, (self.x, self.y, self.width, self.height))
            
            # Cockpit
            pygame.draw.ellipse(screen, DARK_BLUE, (self.x + 10, self.y + 5, 30, 20))
            
            # Wings
            pygame.draw.rect(screen, GRAY, (self.x + 20, self.y - 8, 60, 8))
            pygame.draw.rect(screen, GRAY, (self.x + 20, self.y + self.height, 60, 8))
            
            # Tail
            pygame.draw.polygon(screen, GRAY, [
                (self.x + self.width - 10, self.y + 5),
                (self.x + self.width + 20, self.y - 5),
                (self.x + self.width + 20, self.y + self.height + 5),
                (self.x + self.width - 10, self.y + self.height - 5)
            ])
            
            # Propeller (simple spinning effect)
            prop_center = (self.x + 15, self.y + self.height // 2)
            pygame.draw.circle(screen, BLACK, prop_center, 3)
            angle = pygame.time.get_ticks() * 0.5
            for i in range(3):
                end_x = prop_center[0] + 12 * math.cos(angle + i * 2 * math.pi / 3)
                end_y = prop_center[1] + 12 * math.sin(angle + i * 2 * math.pi / 3)
                pygame.draw.line(screen, BLACK, prop_center, (end_x, end_y), 2)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 45
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.grabbing = False
        self.grab_step = None
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        self.state = "idle"  # idle, running, jumping, grabbing, climbing, parachuting
        self.parachute_active = False
        self.parachute_timer = 0
        
    def start_parachute_jump(self, plane_x, plane_y):
        self.x = plane_x + 50
        self.y = plane_y + 40
        self.vel_y = 1.5
        self.parachute_active = True
        self.parachute_timer = 200  # About 3.3 seconds at 60 FPS
        self.state = "parachuting"
        
    def update(self, steps):
        # Handle parachute landing
        if self.parachute_active:
            self.parachute_timer -= 1
            self.y += self.vel_y
            
            # Check if we should land
            should_land = False
            target_step = None
            
            # Find the landing step
            for step in steps:
                if (abs(self.x + self.width/2 - (step.x + step.width/2)) < step.width/2 + 20 and 
                    step.y > SCREEN_HEIGHT - 200 and 
                    self.y + self.height >= step.y - 20):
                    should_land = True
                    target_step = step
                    break
            
            # Land when timer runs out or when close to a step
            if self.parachute_timer <= 0 or should_land:
                self.parachute_active = False
                self.state = "idle"
                self.vel_y = 0
                
                if target_step:
                    self.y = target_step.y - self.height
                    self.x = target_step.x + target_step.width/2 - self.width/2
                    self.on_ground = True
                else:
                    # Emergency landing
                    self.y = SCREEN_HEIGHT - 150
                    self.on_ground = True
                    
            return None
            
        # Handle input
        keys = pygame.key.get_pressed()
        
        if not self.grabbing:
            # Horizontal movement
            if keys[pygame.K_LEFT]:
                self.vel_x = -MOVE_SPEED
                self.facing_right = False
                if self.on_ground:
                    self.state = "running"
            elif keys[pygame.K_RIGHT]:
                self.vel_x = MOVE_SPEED
                self.facing_right = True
                if self.on_ground:
                    self.state = "running"
            else:
                self.vel_x = 0
                if self.on_ground:
                    self.state = "idle"
            
            # Jumping
            if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
                self.vel_y = JUMP_STRENGTH
                self.on_ground = False
                self.state = "jumping"
                
        else:
            # Climbing logic
            if keys[pygame.K_UP]:
                climbed_step = self.climb_onto_step()
                if climbed_step:
                    return climbed_step
        
        # Apply gravity
        if not self.grabbing:
            self.vel_y += GRAVITY
            
        # Update position
        if not self.grabbing:
            self.x += self.vel_x
            self.y += self.vel_y
            
        # Keep player on screen horizontally
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        
        # Check collisions with steps
        landed_step = self.check_step_collisions(steps)
        
        # Check for grabbing opportunities (improved detection)
        if not self.on_ground and not self.grabbing and self.vel_y > 0:
            self.check_grab_opportunities(steps)
            
        # Update animations
        self.update_animation()
        
        return landed_step
        
    def check_step_collisions(self, steps):
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = False
        
        for step in steps:
            step_rect = pygame.Rect(step.x, step.y, step.width, step.height)
            
            if player_rect.colliderect(step_rect) and self.vel_y >= 0:
                # Landing on top of step
                if self.y < step.y:
                    self.y = step.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                    self.state = "idle"
                    return step
        return None
    
    def check_grab_opportunities(self, steps):
        player_center_x = self.x + self.width / 2
        player_center_y = self.y + self.height / 2
        
        for step in steps:
            step_center_x = step.x + step.width / 2
            step_center_y = step.y + step.height / 2
            
            # Calculate distance to step
            distance = math.sqrt((player_center_x - step_center_x)**2 + 
                               (player_center_y - step_center_y)**2)
            
            # Enhanced grab detection - more forgiving
            vertical_distance = abs(player_center_y - step_center_y)
            horizontal_distance = abs(player_center_x - step_center_x)
            
            # Allow grabbing if player is reasonably close
            if (distance < GRAB_DISTANCE and 
                vertical_distance < 40 and 
                horizontal_distance < step.width/2 + 25 and
                self.y > step.y - 30):
                
                self.grab_step = step
                self.grabbing = True
                self.state = "grabbing"
                self.vel_x = 0
                self.vel_y = 0
                # Position player hanging from step
                self.x = step.x + step.width/2 - self.width/2
                self.y = step.y + step.height
                break
    
    def climb_onto_step(self):
        if self.grab_step:
            self.y = self.grab_step.y - self.height
            self.grabbing = False
            self.on_ground = True
            self.state = "idle"
            climbed_step = self.grab_step
            self.grab_step = None
            return climbed_step
        return None
    
    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= 8:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
    
    def draw_human_sprite(self, screen):
        # Human-like character drawing
        
        # Parachute
        if self.parachute_active:
            parachute_x = self.x + self.width//2
            parachute_y = self.y - 50
            # Parachute canopy
            pygame.draw.arc(screen, RED, (parachute_x - 30, parachute_y, 60, 40), 0, math.pi, 4)
            # Parachute lines
            for i in range(-2, 3):
                line_x = parachute_x + i * 12
                pygame.draw.line(screen, BLACK, (line_x, parachute_y + 20), 
                               (self.x + self.width//2, self.y + 5), 1)
        
        # Head
        head_x = self.x + self.width//2
        head_y = self.y + 8
        pygame.draw.circle(screen, SKIN_COLOR, (int(head_x), int(head_y)), 8)
        
        # Eyes
        eye_offset = 3 if self.facing_right else -3
        pygame.draw.circle(screen, BLACK, (int(head_x + eye_offset), int(head_y - 2)), 2)
        
        # Body
        body_color = BLUE if self.state == "running" else GREEN
        if self.state == "jumping":
            body_color = YELLOW
        elif self.state == "grabbing":
            body_color = RED
            
        pygame.draw.rect(screen, body_color, (self.x + 5, self.y + 16, self.width - 10, 20))
        
        # Arms
        arm_y = self.y + 20
        if self.state == "grabbing":
            # Arms reaching up
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), (self.x + 3, self.y + 5), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 3, self.y + 5), 4)
        elif self.state == "running":
            # Swinging arms
            arm_swing = math.sin(self.animation_frame * 0.8) * 8
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), 
                           (self.x + 8 + arm_swing, arm_y + 12), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 8 - arm_swing, arm_y + 12), 4)
        else:
            # Normal arms
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), (self.x + 8, arm_y + 12), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 8, arm_y + 12), 4)
        
        # Legs
        leg_y = self.y + 36
        if self.state == "running":
            # Running legs animation
            leg_swing = math.sin(self.animation_frame) * 10
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), 
                           (self.x + 8 + leg_swing, leg_y + 15), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 8 - leg_swing, leg_y + 15), 4)
        elif self.state == "jumping":
            # Bent legs for jumping
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), (self.x + 12, leg_y + 10), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 12, leg_y + 10), 4)
        else:
            # Standing legs
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), (self.x + 8, leg_y + 15), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 8, leg_y + 15), 4)
    
    def draw(self, screen):
        self.draw_human_sprite(screen)

class Step:
    def __init__(self, x, y, width, column, step_type="normal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.column = column  # 0=left, 1=middle, 2=right
        self.step_type = step_type  # "easy", "normal", "small"
        self.color = self.get_color()
        
    def get_color(self):
        if self.step_type == "easy":
            return (101, 67, 33)  # Darker brown for easy steps
        elif self.step_type == "small":
            return (160, 82, 45)  # Lighter brown for small steps
        else:
            return BROWN
        
    def update(self, speed):
        self.y -= speed
        
    def draw(self, screen):
        # Main step
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        
        # Add texture lines
        for i in range(0, self.width, 15):
            pygame.draw.line(screen, BLACK, (self.x + i, self.y), (self.x + i, self.y + self.height), 1)
        
        # Add grip texture on top
        for i in range(5, self.width - 5, 10):
            pygame.draw.circle(screen, BLACK, (self.x + i, self.y + 3), 1)

class StepGenerator:
    def __init__(self):
        self.spawn_timer = 0
        self.difficulty = 1.0
        self.last_column = -1
        self.game_start_time = 0
        
    def update(self, steps, game_time):
        # Progressive difficulty - starts easy, gets harder over time
        time_factor = min(game_time / 15000, 1.0)  # Reach max difficulty after 4 minutes
        self.difficulty = 1 + (time_factor * 3)  # Difficulty ranges from 1 to 4
        
        self.spawn_timer += 1
        # Spawn rate increases with difficulty
        base_spawn_rate = 100
        spawn_rate = max(30, int(base_spawn_rate / self.difficulty))
        
        if self.spawn_timer >= spawn_rate:
            self.spawn_step(steps, game_time)
            self.spawn_timer = 0
    
    def spawn_step(self, steps, game_time):
        # Choose column (avoid same column consecutively for better gameplay)
        available_columns = [0, 1, 2]
        if self.last_column != -1 and len(available_columns) > 1:
            available_columns.remove(self.last_column)
        
        column = random.choice(available_columns)
        self.last_column = column
        
        # Progressive step size difficulty
        time_factor = min(game_time / 15000, 1.0)
        easy_probability = EASY_STEP_PROBABILITY_START - (
            (EASY_STEP_PROBABILITY_START - EASY_STEP_PROBABILITY_END) * time_factor
        )
        
        # Determine step size and type
        rand_val = random.random()
        if rand_val < easy_probability:
            # Easy step (large)
            step_width = random.randint(120, 160)
            step_type = "easy"
        elif rand_val < easy_probability + 0.3:
            # Normal step (medium)
            step_width = random.randint(80, 120)
            step_type = "normal"
        else:
            # Small step (challenging)
            step_width = random.randint(50, 80)
            step_type = "small"
        
        # Position based on column with some variation for middle column
        if column == 0:  # Left wall
            x = 50
        elif column == 1:  # Middle (with some horizontal variation)
            base_x = SCREEN_WIDTH // 2 - step_width // 2
            # Add variation but keep it reasonable
            variation = min(80, step_width // 3)
            x = base_x + random.randint(-variation, variation)
            x = max(60, min(SCREEN_WIDTH - step_width - 60, x))  # Keep away from walls
        else:  # Right wall
            x = SCREEN_WIDTH - 50 - step_width
        
        y = SCREEN_HEIGHT + 20
        
        new_step = Step(x, y, step_width, column, step_type)
        steps.append(new_step)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Enhanced Survival Points Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "start"  # start, intro, playing, game_over
        self.score = 0
        self.game_time = 0
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        # Game objects
        self.player = None
        self.plane = Plane()
        self.steps = []
        self.step_generator = StepGenerator()
        self.step_speed = INITIAL_STEP_SPEED
        self.last_step_landed = None
        self.intro_timer = 0
        
    def reset_game(self):
        self.steps = []
        self.score = 0
        self.game_time = 0
        self.step_speed = INITIAL_STEP_SPEED
        self.step_generator = StepGenerator()
        self.last_step_landed = None
        self.intro_timer = 0
        
        # Start intro sequence
        self.game_state = "intro"
        self.plane = Plane()
        self.plane.active = True
        self.player = None
        
        # Create initial large platform for landing
        initial_step = Step(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 120, 200, 1, "easy")
        self.steps.append(initial_step)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_state == "start" and event.key == pygame.K_SPACE:
                    self.reset_game()
                elif self.game_state == "game_over" and event.key == pygame.K_SPACE:
                    self.game_state = "start"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "start":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50)
                    if button_rect.collidepoint(mouse_x, mouse_y):
                        self.reset_game()
    
    def update(self):
        if self.game_state == "intro":
            self.intro_timer += 1
            self.plane.update()
            
            # Player jumps from plane
            if self.plane.should_player_jump() and not self.plane.player_jumped and not self.player:
                self.player = Player(0, 0)
                self.player.start_parachute_jump(self.plane.x, self.plane.y)
                self.plane.player_jumped = True
            
            # Update player during intro (parachute phase)
            if self.player:
                self.player.update(self.steps)
                
                # Switch to playing mode after parachute landing
                if not self.player.parachute_active:
                    self.game_state = "playing"
                    # Ensure player is properly positioned
                    if not self.player.on_ground:
                        for step in self.steps:
                            if step.y > SCREEN_HEIGHT - 200:
                                self.player.y = step.y - self.player.height
                                self.player.x = step.x + step.width/2 - self.player.width/2
                                self.player.on_ground = True
                                break
                
        elif self.game_state == "playing":
            self.game_time += 1
            
            # Update step speed progressively
            time_factor = min(self.game_time / 10000, 1.0)
            self.step_speed = INITIAL_STEP_SPEED + (MAX_STEP_SPEED - INITIAL_STEP_SPEED) * time_factor
            
            # Update player
            landed_step = self.player.update(self.steps)
            if landed_step and landed_step != self.last_step_landed:
                self.score += 1
                self.last_step_landed = landed_step
            
            # Update steps
            for step in self.steps[:]:
                step.update(self.step_speed)
                if step.y < -step.height:
                    self.steps.remove(step)
            
            # Generate new steps
            self.step_generator.update(self.steps, self.game_time)
            
            # Check game over
            if self.player.y > SCREEN_HEIGHT:
                self.game_state = "game_over"
    
    def draw_background(self):
        # Gradient sky background
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(LIGHT_BLUE[0] * (1 - color_ratio) + WHITE[0] * color_ratio)
            g = int(LIGHT_BLUE[1] * (1 - color_ratio) + WHITE[1] * color_ratio)
            b = int(LIGHT_BLUE[2] * (1 - color_ratio) + WHITE[2] * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    def draw_start_screen(self):
        self.draw_background()
        
        # Title with shadow effect
        title_shadow = self.big_font.render("Enhanced Survival Points", True, BLACK)
        title_text = self.big_font.render("Enhanced Survival Points", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        shadow_rect = title_shadow.get_rect(center=(SCREEN_WIDTH//2 + 3, SCREEN_HEIGHT//2 - 97))
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # Animated start button
        button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50)
        button_color = GREEN
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 50
        button_color = (min(255, GREEN[0] + pulse), min(255, GREEN[1] + pulse), GREEN[2])
        
        pygame.draw.rect(self.screen, button_color, button_rect)
        pygame.draw.rect(self.screen, BLACK, button_rect, 3)
        
        button_text = self.font.render("Start Game", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, button_text_rect)
        
        # Instructions
        instructions = [
            "🎮 Arrow keys: Move and jump",
            "🤏 Get close to steps to grab them automatically",
            "⬆️ UP key: Climb onto grabbed steps",
            "🎯 Starts easy, gets progressively harder!",
            "🏆 Survive as long as possible!"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100 + i * 35))
            self.screen.blit(text, text_rect)
    
    def draw_game_over_screen(self):
        self.draw_background()
        
        # Game Over with shadow
        game_over_shadow = self.big_font.render("Game Over", True, BLACK)
        game_over_text = self.big_font.render("Game Over", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        shadow_rect = game_over_shadow.get_rect(center=(SCREEN_WIDTH//2 + 3, SCREEN_HEIGHT//2 - 47))
        self.screen.blit(game_over_shadow, shadow_rect)
        self.screen.blit(game_over_text, game_over_rect)
        
        # Final score
        score_text = self.font.render(f"Final Score: {self.score} steps", True, BLACK)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        self.screen.blit(score_text, score_rect)
        
        # Performance message
        if self.score >= 50:
            perf_msg = "Excellent! You're a master climber!"
        elif self.score >= 30:
            perf_msg = "Great job! You've got good skills!"
        elif self.score >= 15:
            perf_msg = "Not bad! Keep practicing!"
        else:
            perf_msg = "Keep trying! You'll get better!"
            
        perf_text = self.font.render(perf_msg, True, DARK_BLUE)
        perf_rect = perf_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(perf_text, perf_rect)
        
        # Restart instruction
        restart_text = self.font.render("Press SPACE to return to menu", True, BLACK)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
        self.screen.blit(restart_text, restart_rect)
    
    def draw_game(self):
        self.draw_background()
        
        # Draw textured walls
        wall_segments = SCREEN_HEIGHT // 25
        for i in range(wall_segments):
            y = i * 25
            # Left wall
            color_variation = 20 if i % 2 == 0 else 0
            wall_color = (GRAY[0] + color_variation, GRAY[1] + color_variation, GRAY[2] + color_variation)
            pygame.draw.rect(self.screen, wall_color, (0, y, 50, 25))
            pygame.draw.rect(self.screen, BLACK, (0, y, 50, 25), 1)
            
            # Right wall
            pygame.draw.rect(self.screen, wall_color, (SCREEN_WIDTH - 50, y, 50, 25))
            pygame.draw.rect(self.screen, BLACK, (SCREEN_WIDTH - 50, y, 50, 25), 1)
        
        # Draw steps
        for step in self.steps:
            step.draw(self.screen)
        
        # Draw plane during intro
        if self.game_state == "intro":
            self.plane.draw(self.screen)
        
        # Draw player
        if self.player:
            self.player.draw(self.screen)
        
        # UI Elements
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        score_bg = pygame.Rect(5, 5, score_text.get_width() + 10, score_text.get_height() + 10)
        pygame.draw.rect(self.screen, WHITE, score_bg)
        pygame.draw.rect(self.screen, BLACK, score_bg, 2)
        self.screen.blit(score_text, (10, 10))
        
        # Speed indicator
        speed_text = self.font.render(f"Speed: {self.step_speed:.1f}x", True, BLACK)
        speed_bg = pygame.Rect(5, 50, speed_text.get_width() + 10, speed_text.get_height() + 10)
        pygame.draw.rect(self.screen, WHITE, speed_bg)
        pygame.draw.rect(self.screen, BLACK, speed_bg, 2)
        self.screen.blit(speed_text, (10, 55))
        
        # Difficulty indicator
        difficulty_level = int(self.step_generator.difficulty)
        diff_text = self.font.render(f"Difficulty: {difficulty_level}/4", True, BLACK)
        diff_bg = pygame.Rect(5, 95, diff_text.get_width() + 10, diff_text.get_height() + 10)
        pygame.draw.rect(self.screen, WHITE, diff_bg)
        pygame.draw.rect(self.screen, BLACK, diff_bg, 2)
        self.screen.blit(diff_text, (10, 100))
        
        # Grabbing instruction
        if self.player and self.player.grabbing:
            grab_text = self.big_font.render("Press UP to climb!", True, RED)
            grab_bg = pygame.Rect(SCREEN_WIDTH//2 - grab_text.get_width()//2 - 10, 80, 
                                grab_text.get_width() + 20, grab_text.get_height() + 10)
            pygame.draw.rect(self.screen, WHITE, grab_bg)
            pygame.draw.rect(self.screen, RED, grab_bg, 3)
            grab_rect = grab_text.get_rect(center=(SCREEN_WIDTH//2, 90))
            self.screen.blit(grab_text, grab_rect)
    
    def draw(self):
        if self.game_state == "start":
            self.draw_start_screen()
        elif self.game_state in ["intro", "playing"]:
            self.draw_game()
        elif self.game_state == "game_over":
            self.draw_game_over_screen()
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
